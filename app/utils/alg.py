import asyncio
from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from app.config import TIMEZONE
from app.services.event_checker import BookingCallbackData
from app.utils.websockets import notify_users
from app.utils.words import get_russion_table_name


def max_zeros_between_ones(arr):
    indices_of_ones = [i for i, x in enumerate(arr) if x == 1]
    if len(indices_of_ones) < 2:
        return 0
    max_zeros = 0
    for i in range(1, len(indices_of_ones)):
        zeros_between = indices_of_ones[i] - indices_of_ones[i - 1] - 1
        max_zeros = max(max_zeros, zeros_between)
    return max_zeros


def get_max_zero_block_start(arr, zeros):
    current_zeros = 0
    start_index = None

    for i, x in enumerate(arr):
        if x == 0:
            if current_zeros == 0:
                start_index = i
            current_zeros += 1
        else:
            current_zeros = 0

        if current_zeros == zeros:
            return start_index

    return 0


async def check_queue_entry(booking_service, queue_service, queue_entry, booking, now, booking_time_start, timelines, user_id):
    if queue_entry.user.id == user_id:
        return False

    checker_start = queue_entry.date
    if checker_start is None:
        checker_start = now + timedelta(hours=1)

    end_hours = checker_start.hour + queue_entry.hours
    if queue_entry.date.date() != booking_time_start.date():
        return False

    max_hours = max(
        max_zeros_between_ones(timeline[checker_start.hour:end_hours]) if sum(timeline) != 0 else 24 
        for timeline in timelines
    )

    if queue_entry.hours > max_hours:
        return False
    
    start_hour = get_max_zero_block_start(timelines[checker_start.hour:end_hours], max_hours)
    start_day, start_hour = divmod(start_hour + checker_start.hour, 24)
    start_date = checker_start.replace(day=checker_start.day + start_day, hour=start_hour)
    time_end = start_date + timedelta(hours=queue_entry.hours)

    try:
        new_booking = await booking_service.create_booking(
            table_id=booking.table.id,
            time_start=start_date.replace(tzinfo=None),
            time_end=time_end.replace(tzinfo=None),
            features=[],
            comment=queue_entry.comment,
            people_amount=1,
            location_id=booking.table.location_id,
            table_name=booking.table.table_name,
            user_id=queue_entry.user.id
        )
        asyncio.create_task(notify_users(
            new_booking.table.location_id,
            {
                "event": "booking_created",
                "table_id": new_booking.table.table_name,
                "time_start": str(new_booking.time_start),
                "time_end": str(new_booking.time_end),
            },
        ))
        await queue_service.queue.delete(queue_entry.id)

        from app.bot import get_bot

        message = (
            "✅ Вы встали в очередь и мы забронировали вам место:\n"
            f"• Место: {get_russion_table_name(booking.table.table_name)}\n"
        )
        builder = InlineKeyboardBuilder()
        callback_data = BookingCallbackData(
            action="start",
            booking_id=booking.id,
        ).pack()
        
        builder.add(
            types.InlineKeyboardButton(
                text="❌ Отменить бронь", callback_data=callback_data
            )
        )
        try:
            await get_bot().send_message(
                chat_id=queue_entry.user.id,
                text=message,
                reply_markup=builder.as_markup()
            )
        except:
            pass
        return True
    except:
        return False

async def handle_additional_operations(booking, queue_service, tables_service, booking_service, now, user_id):
    booking_time_start = booking.time_start
    location_id = booking.table.location.id
    timelines = await tables_service.repo.get_bookings_timelines(
        location_id, booking.time_start.date(), is_two_days=True
    )

    for queue_entry in await queue_service.get_location_queues_by_day(
        booking.table.location.id, booking.time_start.date()
    ):
    
        result = await check_queue_entry(booking_service, queue_service, queue_entry, booking, now, booking_time_start, timelines, user_id)
        if result:
            timelines = await tables_service.repo.get_bookings_timelines(
                location_id, booking.time_start.date(), is_two_days=True
            )