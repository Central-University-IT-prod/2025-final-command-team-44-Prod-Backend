import asyncio
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)

from app.api.dependencies import (
    CurrentUser,
    CurrentWsUser,
    get_exist_location,
    get_user_booking,
)
from app.config import TIMEZONE, active_connections
from app.infra.database.models import Booking, BookingUserStatusEnum, Location, Table
from app.schemas.booking import BookingResponse, CreateBooking, UpdateBooking
from app.services import BookingService
from app.services.queue import QueueService
from app.services.table import TableService
from app.utils.alg import handle_additional_operations
from app.utils.websockets import notify_users

router = APIRouter(prefix="/booking", tags=["Пользовательское бронирование"])


async def get_exist_location_table(
    table_name: str,
    location: Location = Depends(get_exist_location),
    table_service: TableService = Depends(TableService),
):
    table = await table_service.repo.find_one(
        table_name=table_name, location_id=location.id
    )

    if not table:
        raise HTTPException(status_code=404, detail="Место не найдено.")

    return table


async def validate_put_booking(data: CreateBooking, table: Table):
    time_end: datetime = data.time_start + timedelta(hours=data.hours)

    if data.time_start.hour < table.location.open_hour:
        raise HTTPException(
            status_code=400, detail="Нельзя забронировать место до открытия коворкинга."
        )

    if data.time_start.hour + data.hours > table.location.close_hour:
        raise HTTPException(
            status_code=400,
            detail="Нельзя забронировать место после закрытия коворкинга.",
        )

    if data.people_amount > table.max_people_amount:
        raise HTTPException(
            status_code=400, detail="Нельзя пригласить больше людей, чем вмещает бронь."
        )

    return time_end


async def validate_changed_time(
    data: CreateBooking,
    booking: Booking,
    table_service: TableService,
    booking_service: BookingService,
):
    now = datetime.now(TIMEZONE)

    time_start = data.time_start
    time_end = data.time_start + timedelta(hours=data.hours)

    if time_end < now:
        raise HTTPException(status_code=409, detail="Бронирование уже закончилось.")

    if time_start < booking.time_start:
        raise HTTPException(
            status_code=409,
            detail="Нельзя изменить дату начала брони, когда она уже началась.",
        )

    if time_start >= time_end:
        raise HTTPException(
            status_code=409, detail="Начало брони должно быть меньше, чем её конец."
        )

    table = await table_service.repo.get(booking.table_id)

    if (
        booking.table.location.open_hour != 0
        and booking.table.location.close_hour != 24
    ):
        if time_start.hour < booking.table.location.open_hour:
            raise HTTPException(
                status_code=404,
                detail="Нельзя забронировать место до открытия коворкинга.",
            )

        if time_end.hour > booking.table.location.close_hour:
            raise HTTPException(
                status_code=404,
                detail="Нельзя забронировать место после закрытия коворкинга.",
            )

    if not await booking_service.is_booking_avalale(
        table.table_name,
        booking.table.location_id,
        data.time_start,
        time_end,
        ignore=booking.id,
    ):
        raise HTTPException(status_code=409, detail="Это время уже забронировано.")

    return time_end


@router.post(
    "/{location_id}/{table_name}",
    summary="Создание бронирования",
    status_code=201,
    response_model=BookingResponse,
)
async def create_booking(
    user: CurrentUser,
    create_data: CreateBooking,
    table: Table = Depends(get_exist_location_table),
    booking_service: BookingService = Depends(BookingService),
):
    time_end = await validate_put_booking(data=create_data, table=table)

    booking = await booking_service.create_booking(
        table_id=table.id,
        time_start=create_data.time_start,
        time_end=time_end,
        features=create_data.features,
        comment=create_data.comment,
        people_amount=create_data.people_amount,
        location_id=table.location.id,
        table_name=table.table_name,
        user_id=user.id,
    )

    asyncio.create_task(
        notify_users(
            table.location_id,
            {
                "event": "booking_created",
                "table_id": booking.table.table_name,
                "time_start": str(create_data.time_start),
                "time_end": str(time_end),
            },
        )
    )

    return BookingResponse(
        **booking.to_dict(),
        location_id=booking.table.location_id,
        table_name=booking.table.table_name,
    )


@router.delete("/{booking_id}", summary="Отмена бронирования", status_code=204)
async def cancel_booking(
    user: CurrentUser,
    booking: Booking = Depends(get_user_booking),
    booking_service: BookingService = Depends(BookingService),
    queue_service: QueueService = Depends(QueueService),
    tables_service: TableService = Depends(TableService),
):
    now = datetime.now(TIMEZONE)

    if booking.time_end < now:
        raise HTTPException(status_code=409, detail="Бронирование уже закончилось.")

    book_member = await booking_service.get_user_booking_by_user_id(
        booking_id=booking.id, user_id=user.id
    )

    if not book_member or book_member.status != BookingUserStatusEnum.creator:
        raise HTTPException(
            status_code=403, detail="Вы не имеете доступ к отмене бронирования."
        )

    await booking_service.repo.delete(booking.id)

    now = datetime.now(TIMEZONE).replace(minute=0, second=0, microsecond=0)
    asyncio.create_task(
        notify_users(
            booking.table.location_id,
            {
                "event": "booking_canceled",
                "table_id": booking.table.table_name,
                "time_start": str(booking.time_start),
                "time_end": str(booking.time_end),
            },
        )
    )

    if booking.table.max_people_amount == 1:
        asyncio.create_task(
            handle_additional_operations(
                booking, queue_service, tables_service, booking_service, now, user.id
            )
        )
    return Response(status_code=204)


@router.put(
    "/{booking_id}",
    status_code=200,
    response_model=BookingResponse,
    summary="Изменение бронирования",
)
async def update_booking(
    user: CurrentUser,
    update_data: UpdateBooking,
    booking: Booking = Depends(get_user_booking),
    booking_service: BookingService = Depends(BookingService),
    queue_service: QueueService = Depends(QueueService),
    tables: TableService = Depends(TableService),
):
    time_end = update_data.time_start + timedelta(hours=update_data.hours)

    await validate_changed_time(
        data=update_data,
        booking=booking,
        table_service=tables,
        booking_service=booking_service,
    )

    response = await booking_service.repo.update(
        booking.id,
        features=update_data.features,
        comment=update_data.comment,
        time_start=update_data.time_start,
        time_end=time_end,
    )
    asyncio.create_task(
        notify_users(
            booking.table.location_id,
            {
                "event": "booking_updated",
                "table_id": booking.table.table_name,
                "time_start": str(update_data.time_start),
                "time_end": str(time_end),
            },
        )
    )
    if booking.table.max_people_amount == 1:
        now = datetime.now(TIMEZONE).replace(minute=0, second=0, microsecond=0)
        asyncio.create_task(
            handle_additional_operations(
                booking, queue_service, tables, booking_service, now, user.id
            )
        )
    return BookingResponse(
        **response.to_dict(),
        table_name=response.table.table_name,
        location_id=response.table.location_id,
    )


@router.websocket("/ws/{location_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user: CurrentWsUser,
    location: Location = Depends(get_exist_location),
):
    await websocket.accept()
    if not active_connections.get(location.id):
        active_connections[location.id] = {user.id: websocket}
    else:
        active_connections[location.id][user.id] = websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        del active_connections[location.id][user.id]
