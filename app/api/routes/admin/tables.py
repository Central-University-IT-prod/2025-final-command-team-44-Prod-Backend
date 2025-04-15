import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.dependencies import CurrentAdmin, get_admin_location_table_name, get_admin_location_table
from app.api.routes.user.book import validate_changed_time, validate_put_booking
from app.config import TIMEZONE
from app.infra.database.models import Table
from app.schemas.booking import (
    BookingAdminResponse,
    CreateBookingAdmin,
    UpdateBooking,
    UserBookingForAdmin,
)
from app.schemas.tables import *
from app.services.booking import BookingService
from app.services.queue import QueueService
from app.services.table import TableService
from app.services.user import UserService
from app.utils.alg import handle_additional_operations
from app.utils.websockets import notify_users

router = APIRouter(prefix="/tables", tags=["Управление столами в зале"])


@router.get(
    "/{location_id}/{table_name}",
    summary="Получение мест админом",
    response_model=TableResponse,
)
async def get_table(
    table: Table = Depends(get_admin_location_table_name),
):
    return table.to_dict()


@router.get(
    "/{location_id}/{table_name}/bookings",
    summary="Получить все брони у мест",
    response_model=List[BookingAdminResponse],
)
async def table_bookings_admin(
    admin: CurrentAdmin,
    table: Table = Depends(get_admin_location_table_name),
    service: TableService = Depends(TableService),
):
    return [
        BookingAdminResponse(
            id=entry.id,
            location_id=entry.table.location.id,
            code=entry.code,
            table_id=entry.table.id,
            table_name=entry.table.table_name,
            time_start=entry.time_start,
            time_end=entry.time_end,
            comment=entry.comment,
            features=entry.features,
            people_amount=entry.people_amount,
            users=[
                UserBookingForAdmin(
                    id=bookuser.id,
                    first_name=bookuser.user.first_name,
                    username=bookuser.user.username,
                    user_id=bookuser.user.id,
                    status=bookuser.status,
                )
                for bookuser in entry.users
            ],
        )
        for entry in await service.repo.get_table_bookings(table.id, admin.id)
    ]


@router.patch(
    "/{location_id}/{table_id}/{booking_id}",
    summary="Обновить бронь у места",
    response_model=BookingAdminResponse,
)
async def update_booking_admin(
    _: CurrentAdmin,
    update_data: UpdateBooking,
    booking_id: str,
    table: Table = Depends(get_admin_location_table),
    booking_service: BookingService = Depends(BookingService),
    table_service: TableService = Depends(TableService),
    queue_service: QueueService = Depends(QueueService),
    tables_service: TableService = Depends(TableService),
):
    booking = await booking_service.repo.get(booking_id)
    if booking.table_id != table.id:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    time_end = update_data.time_start + timedelta(hours=update_data.hours)
    await validate_changed_time(
        data=update_data,
        booking=booking,
        table_service=table_service,
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
                booking, queue_service, tables_service, booking_service, now, 1
            )
        )
    return BookingAdminResponse(
        id=response.id,
        location_id=response.table.location.id,
        code=response.code,
        table_id=response.table.id,
        table_name=response.table.table_name,
        time_start=response.time_start,
        time_end=response.time_end,
        comment=response.comment,
        features=response.features,
        people_amount=response.people_amount,
        users=[
            UserBookingForAdmin(
                id=bookuser.id,
                first_name=bookuser.user.first_name,
                username=bookuser.user.username,
                user_id=bookuser.user.id,
                status=bookuser.status,
            )
            for bookuser in response.users
        ],
    )


@router.delete(
    "/{location_id}/{table_id}/{booking_id}",
    summary="Удалить бронь у места",
    status_code=204,
)
async def delete_booking_admin(
    _: CurrentAdmin,
    booking_id: str,
    table: Table = Depends(get_admin_location_table),
    booking_service: BookingService = Depends(BookingService),
    queue_service: QueueService = Depends(QueueService),
    tables_service: TableService = Depends(TableService),
):
    booking = await booking_service.repo.get(booking_id)
    if booking.table_id != table.id:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    await booking_service.repo.delete(booking.id)
    asyncio.create_task(
        notify_users(
            booking.table.location_id,
            {
                "event": "booking_canceled",
                "table_id": booking.table.table_name,
            },
        )
    )
    if booking.table.max_people_amount == 1:
        now = datetime.now(TIMEZONE).replace(minute=0, second=0, microsecond=0)
        asyncio.create_task(
            handle_additional_operations(
                booking, queue_service, tables_service, booking_service, now, 1
            )
        )
    return Response(status_code=204)


@router.patch(
    "/{location_id}/{table_id}",
    summary="Обновление места админом",
    response_model=TableResponse,
)
async def update_table(
    data: TablePatch,
    table: Table = Depends(get_admin_location_table),
    service: TableService = Depends(TableService),
):
    table = await service.repo.update(
        id=table.id, features=data.features, max_people_amount=data.max_people_amount
    )
    return table.to_dict()


@router.post(
    "/{location_id}/{table_id}",
    summary="Создание бронирования админом",
    status_code=201,
    response_model=BookingAdminResponse,
)
async def create_booking(
    _: CurrentAdmin,
    create_data: CreateBookingAdmin,
    table: Table = Depends(get_admin_location_table),
    booking_service: BookingService = Depends(BookingService),
    user_service: UserService = Depends(UserService),
):
    user = await user_service.repo.find_one(phone=create_data.phone_number)
    if not user:
        raise HTTPException(
            404, detail="Пользователь с таким номером телефона не найден."
        )

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

    user_booking = await booking_service.booking_users.find_one(
        status="creator", booking_id=booking.id
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

    return BookingAdminResponse(
        id=booking.id,
        location_id=booking.table.location.id,
        code=booking.code,
        table_id=booking.table.id,
        table_name=booking.table.table_name,
        time_start=booking.time_start,
        time_end=booking.time_end,
        comment=booking.comment,
        features=booking.features,
        people_amount=booking.people_amount,
        users=[
            UserBookingForAdmin(
                id=user_booking.id,
                first_name=user_booking.user.first_name,
                username=user_booking.user.username,
                user_id=user_booking.user.id,
                status=user_booking.status,
            )
        ],
    )
