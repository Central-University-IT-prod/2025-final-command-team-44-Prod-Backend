import asyncio
from datetime import datetime, timedelta

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import TIMEZONE
from app.infra.database.models import (
    Booking,
    BookingUser,
    BookingUserStatusEnum,
    QueueUser,
    Table,
)
from app.infra.database.session import async_session
from app.utils.websockets import notify_users
from app.utils.words import get_russion_table_name


class BookingCallbackData(CallbackData, prefix="bc"):
    booking_id: str
    action: str


class EventChecker:
    def __init__(self):
        self.tz = TIMEZONE
        self.scheduler = AsyncIOScheduler(timezone=str(self.tz))
        self.last_check = datetime.now(self.tz)

    async def start(self):
        self.scheduler.add_job(
            self._check_and_notify_bookings, "interval", seconds=5, max_instances=1
        )
        self.scheduler.start()

    async def _check_and_notify_bookings(self):
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(QueueUser).filter(QueueUser.date < datetime.now())
                )
                old_records = result.scalars().all()

                for record in old_records:
                    await session.delete(record)

                await session.commit()
                await self._process_active_bookings(session)
                await self._process_completed_bookings(session)
                await self._process_start_bookings(session)
                await self._process_start_booking_notification_for_websocket(session)

            except Exception as e:
                print(f"Error processing bookings: {str(e)}")

    async def _process_start_bookings(self, session):
        now = datetime.now(self.tz)

        start_bookings = await self._get_bookings(
            session,
        )

        # print(f"start -- {start_bookings}")

        def debug(b):
            # print("_))))0")
            # print(b.time_start, now + timedelta(hours=4))
            return (
                b.time_start <= now + timedelta(hours=4)
                and b.notification_sent_start == False
            )

        start_bookings = list(
            filter(
                debug,
                start_bookings,
            )
        )

        # print(f"filtered start -- {start_bookings}")

        for booking in start_bookings:
            await self._notify_users_about_start(booking)
            booking.notification_sent_start = True
            await session.commit()

    async def _process_active_bookings(self, session):
        now = datetime.now(TIMEZONE)

        notification_time = now + timedelta(hours=3, minutes=10)

        active_bookings = await self._get_bookings(
            session,
        )

        # print(f"active -- {active_bookings}")

        active_bookings = list(
            filter(
                lambda b: b.time_end <= notification_time
                and b.time_end > now
                and b.notification_sent == False,
                active_bookings,
            )
        )

        # print(f"filter active -- {active_bookings}")

        for booking in active_bookings:
            # print("booking -- ")
            # print(booking)
            await self._notify_users(booking)
            booking.notification_sent = True
            await session.commit()

    async def _process_completed_bookings(self, session):
        completed_bookings = await self._get_bookings(
            session,
        )

        completed_bookings = list(
            filter(
                lambda b: b.time_end <= datetime.now(self.tz) + timedelta(hours=3)
                and b.notification_for_fronted_about_canceled is False,
                completed_bookings,
            )
        )

        for booking in completed_bookings:
            await self._notify_booking_completion(booking)
            booking.notification_for_fronted_about_canceled = True
            await session.commit()

    async def _get_bookings(
        self,
        session,
    ):
        stmt = select(Booking).options(
            joinedload(Booking.users).joinedload(BookingUser.user),
            joinedload(Booking.table).joinedload(Table.location),
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def _notify_users(self, booking: Booking):
        for booking_user in booking.users:
            if booking_user.user.id:
                if booking_user.status == BookingUserStatusEnum.creator:
                    print(
                        f"---> send noti for user ({booking_user.user.id}) and booking {booking}"
                    )
                    await self._send_booking_reminder(
                        chat_id=booking_user.user.id,
                        booking=booking,
                    )

    async def _notify_users_about_start(self, booking: Booking):
        for booking_user in booking.users:
            if booking_user.user.id:
                if booking_user.status == BookingUserStatusEnum.creator:
                    print(
                        f"---> send noti for user ({booking_user.user.id}) and booking {booking} about start booking"
                    )
                    await self._send_booking_about_start(
                        chat_id=booking_user.user.id,
                        booking=booking,
                    )

    async def _send_booking_about_start(
        self,
        chat_id: int,
        booking: Booking,
    ):
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

        time_difference = (
            booking.time_start - datetime.now(TIMEZONE) - timedelta(hours=3)
        )
        minutes_until_start = int(time_difference.total_seconds() / 60) + 1

        message = (
            "⌚ Ваша бронь скоро начнётся.\n"
            f"• Место: {get_russion_table_name(booking.table.table_name)}\n"
            f"• Начало через: {minutes_until_start}мин\n"
        )

        from app.bot import get_bot

        print(f"---> send notif about start for user ({chat_id}) and message {message}")
        
        try:
            await get_bot().send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown",
            )
        except:
            pass

    async def _send_booking_reminder(
        self,
        chat_id: int,
        booking: Booking,
    ):
        builder = InlineKeyboardBuilder()
        callback_data = BookingCallbackData(
            action="extend",
            booking_id=booking.id,
        ).pack()

        builder.add(
            types.InlineKeyboardButton(
                text="↳ Продлить на час?", callback_data=callback_data
            )
        )

        time_difference = booking.time_end - datetime.now(TIMEZONE) - timedelta(hours=3)
        minutes_until_end = int(time_difference.total_seconds() / 60) + 1

        message = (
            "⏳ Ваша бронь скоро заканчивается.\n"
            f"• Место: {get_russion_table_name(booking.table.table_name)}\n"
            f"• Осталось: {minutes_until_end}мин\n"
            "Пожалуйста, подумайте о продлении."
        )

        from app.bot import get_bot

        print(f"---> send noti for user ({chat_id}) and message {message}")

        try:
            await get_bot().send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown",
            )
        except:
            pass

    async def _process_start_booking_notification_for_websocket(self, session):
        start_bookings = await self._get_bookings(
            session,
        )

        start_bookings = list(
            filter(
                lambda b: b.time_start <= datetime.now(self.tz) + timedelta(hours=3)
                and b.notification_for_fronted_about_start == False,
                start_bookings,
            )
        )

        for booking in start_bookings:
            await self._notify_booking_start(booking)
            booking.notification_for_fronted_about_start = True
            await session.commit()

    async def _notify_booking_start(self, booking: Booking):
        print(
            f"---> send noti about start for table ({booking.table_id}) and event `booking_canceled`"
        )
        asyncio.create_task(notify_users(
            booking.table.location_id,
            {
                "event": "booking_started",
                "table_id": booking.table.table_name,
                "time_start": str(booking.time_start),
                "time_end": str(booking.time_end),
            },
        ))

    async def _notify_booking_completion(self, booking: Booking):
        print(
            f"---> send noti about close for table ({booking.table_id}) and event `booking_canceled`"
        )
        asyncio.create_task(notify_users(
            booking.table.location_id,
            {
                "event": "booking_canceled",
                "table_id": booking.table.table_name,
                "time_start": str(booking.time_start),
                "time_end": str(booking.time_end),
            },
        ))
