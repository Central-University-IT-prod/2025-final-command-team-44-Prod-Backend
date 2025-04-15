import asyncio
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.dependencies import CurrentUser, get_exist_location
from app.config import TIMEZONE
from app.infra.database.models import Location
from app.schemas.queue import JoinQueue, QueueReponse
from app.services.booking import BookingService
from app.services.queue import QueueService
from app.services.table import TableService
from app.utils.websockets import notify_users

router = APIRouter(prefix="/queue", tags=["Очередь"])


@router.post(
    "/{location_id}",
    status_code=204,
)
async def join_queue(
    queue_data: JoinQueue,
    user: CurrentUser,
    queue: QueueService = Depends(QueueService),
    table_service: TableService = Depends(TableService),
    location: Location = Depends(get_exist_location),
    booking_service: BookingService = Depends(BookingService),
):
    if queue_data.date:
        start_date = queue_data.date
        end_date = start_date + timedelta(hours=queue_data.hours)
    else:
        start_date = datetime.now(TIMEZONE).replace(
            minute=0, second=0, microsecond=0, tzinfo=None
        ) + timedelta(hours=1)
        end_date = start_date + timedelta(hours=queue_data.hours)

    if await queue.get_user_queues_by_day(user.id, start_date.date()):
        raise HTTPException(
            status_code=409, detail="У вас уже есть активная очередь на этот день"
        )

    if start_date.hour < location.open_hour or end_date.hour >= location.close_hour:
        raise HTTPException(
            status_code=400,
            detail="Нельзя забронировать место в нерабочее время коворкинга.",
        )

    booking_tables = [(booking.table.id, booking.table.table_name, booking.table.max_people_amount) for booking in await table_service.repo.get_count_bookings(location.id, start_date, end_date)]
    all_booking_tables = [(table.id, table.table_name, table.max_people_amount) for table in await table_service.repo.get_total_tables(location.id)]
    if len(booking_tables) != len(all_booking_tables):
        tables = set(all_booking_tables) - set(booking_tables)
        for table in tables:
            if table[2] != 1:
                continue

            booking = await booking_service.create_booking(
                table_id=table[0],
                time_start=start_date,
                time_end=end_date,
                features=[],
                comment=None,
                people_amount=1,
                location_id=location.id,
                table_name=table[1],
                user_id=user.id,
            )
            asyncio.create_task(
                notify_users(
                    booking.table.location_id,
                    {
                        "event": "booking_created",
                        "table_id": booking.table.table_name,
                        "time_start": str(booking.time_start),
                        "time_end": str(booking.time_end),
                    },
                )
            )
            return Response(status_code=204)

    await queue.add_user(user.id, start_date, queue_data.hours, location.id)
    return Response(status_code=204)


@router.delete(
    "/{location_id}/{queue_id}",
    status_code=204,
)
async def cancel_queue(
    queue_id: str,
    user: CurrentUser,
    queue_service: QueueService = Depends(QueueService),
    _: Location = Depends(get_exist_location),
):
    queue = await queue_service.queue.get(queue_id)
    if queue.user_id != user.id:
        raise HTTPException(403, "Вы не можете отменить эту очередь")

    await queue_service.queue.delete(queue_id)
    return Response(status_code=204)


@router.get("/", status_code=200, response_model=List[QueueReponse])
async def get_user_queues(
    user: CurrentUser,
    queue_service: QueueService = Depends(QueueService),
):
    return await queue_service.queue.get_user_queues(user.id)
