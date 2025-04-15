import asyncio
from datetime import date, datetime
from typing import List

from aiogram import F, Router
from app.bot.utils import Message
from app.config import TIMEZONE, BASE_DIR
from app.exceptions import ServiceException
from app.infra.database.models import Booking
from app.infra.repository import UserRepository
from app.infra.repository import AdminRepository
from app.services import BookingService, QueueService, TableService
from app.utils.alg import handle_additional_operations
from app.utils.websockets import notify_users

router_all_booking = Router()



ADMIN = dict(id="admin_demo_id", login="admin_demo", password=f"abcd123")

LOCATION = dict(id=f"location_1_id", name="Яхонты",
            address=f"Ногинск", open_hour=0, close_hour=24, admin_id = ADMIN['id'])

@router_all_booking.message(F.text.startswith("/clear_one"))
async def clear(message: Message):
    await AdminRepository().get_or_create(**ADMIN)

    location = await message.bot.location.repo.get_or_create(**LOCATION)

    bookings: List[Booking] = await message.bot.booking.get_location_bookings(location_id=location.id, admin_id=ADMIN['id'])

    now = datetime.now(TIMEZONE).replace(minute=0, second=0, microsecond=0)
    
    booking = bookings[0]
    
    await message.bot.booking.repo.delete(booking.id)
    await asyncio.create_task(handle_additional_operations(booking, QueueService(), TableService(), BookingService(), now, 0))

    await message.answer(f'Бронь отменена {booking.id} {booking.table}')


@router_all_booking.message(F.text.startswith("/book_all"))
async def book_all(message: Message):
    await AdminRepository().get_or_create(**ADMIN)

    location = await message.bot.location.repo.get_or_create(**LOCATION)
    with open(BASE_DIR.joinpath('src/judge-room.svg'), 'rb') as f:
        content = f.read()
    await message.bot.location.set_svg(location_id=location.id, svg=content)

    tables = await message.bot.tables.repo.find(location_id=location.id)

    day = datetime.now().date().day

    time_start = datetime(year=2025, month=3, day=day, hour=1,
                          minute=0, second=0, microsecond=0, tzinfo=None)
    time_end = datetime(year=2025, month=3, day=day, hour=23,
                        minute=0, second=0, microsecond=0, tzinfo=None)

    for i in range(len(tables)):
        table = tables[i]

        user_data = dict(username=f"TestUser{i}", id=int(i), first_name=f"TestUser{i}")
        await UserRepository().get_or_create(**user_data)

        await message.bot.booking.create_booking(
            table_id=table.id,
            time_start=time_start,
            time_end=time_end,
            features=[],
            comment='auto',
            people_amount=1,
            location_id=location.id,
            table_name=table.table_name,
            user_id=user_data['id']
        )
    await message.answer('OK')
