import asyncio
from datetime import datetime, time, timedelta

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import selectinload

from app.config import TIMEZONE
from app.infra.database.models import Booking, BookingUserStatusEnum, Table
from app.infra.repository.booking import BookingRepository
from app.services.booking import BookingService
from app.services.event_checker import BookingCallbackData
from app.utils.websockets import notify_users

router_notification = Router()


@router_notification.callback_query(BookingCallbackData.filter(F.action == "extend"))
async def handle_booking_extension(
    callback: types.CallbackQuery, callback_data: BookingCallbackData, state: FSMContext
):
    try:
        booking_id = callback_data.booking_id

        booking_service = BookingService()

        # async with BookingRepository.session() as session:
        booking = await booking_service.repo.get(
            booking_id,
            options=[selectinload(Booking.table).selectinload(Table.location)],
        )

        if not booking:
            return await callback.answer("⚠️ Бронь не найдена", show_alert=True)

        tz = TIMEZONE
        now = datetime.now(tz)

        close_hour = (
            booking.table.location.close_hour
            if booking.table.location.close_hour != 24
            else 0
        )

        close_time = tz.localize(
            datetime.combine(
                booking.time_start.astimezone(tz).date(), time(hour=close_hour)
            )
        ) + timedelta(hours=3)

        current_end = booking.time_end

        new_end_time = current_end + timedelta(hours=1)

        if new_end_time > close_time:
            return await callback.answer(
                "⚠️ Продление после закрытия невозможно",
                show_alert=True,
            )

        is_available = await booking_service.is_booking_avalale(
            table_name=booking.table_id,
            time_start=current_end,
            time_end=new_end_time,
            location_id=booking.table.location_id,
        )

        if not is_available:
            return await callback.answer(
                "⚠️ Временной слот занят",
                show_alert=True,
            )

        await booking_service.repo.update(
            booking.id,
            time_end=new_end_time,
        )

        # booking.time_end = new_end_time
        # await session.commit()

        await notify_users(
            location_id=booking.table.location_id,
            message={
                "event": "booking_created",
                "table_id": booking.table_id,
                "time_start": current_end,
                "time_end": new_end_time,
            },
        )

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(
            f"✅ Бронь продлена до {new_end_time.strftime('%H:%M')}"
        )
        await callback.answer()

    except Exception as e:
        await callback.answer("⚠️ Ошибка при продлении", show_alert=True)


@router_notification.callback_query(BookingCallbackData.filter(F.action == "start"))
async def handle_booking_start_cancel(
    callback: types.CallbackQuery, callback_data: BookingCallbackData, state: FSMContext
):
    try:
        booking_id = callback_data.booking_id

        async with BookingRepository.session() as session:
            booking = await session.get(Booking, booking_id)
            if not booking:
                return await callback.answer("⚠️ Бронь не найдена", show_alert=True)

            now = datetime.now(TIMEZONE)

            if booking.time_end < now:
                return await callback.answer(
                    "⚠️ К Бронирование уже закончилось.",
                    show_alert=True,
                )

            booking_service = BookingService()

            book_member = await booking_service.get_user_booking_by_user_id(
                booking_id=booking.id, user_id=callback.message.chat.id
            )
            if not book_member or book_member.status != BookingUserStatusEnum.creator:
                return await callback.answer(
                    "⚠️ Вы не имеете доступ к отмене бронирования.",
                    show_alert=True,
                )

            await booking_service.repo.delete(booking.id)

            if booking.time_start < now:
                asyncio.create_task(notify_users(
                    booking.table.location_id,
                    {
                        "event": "booking_canceled",
                        "table_id": booking.table.table_name,
                        "time_start": str(booking.time_start),
                        "time_end": str(booking.time_end),
                    },
                ))

            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.edit_text("✅ Бронь успешно отменена!")
            await callback.answer(
                "✅ Бронь успешно отмена!",
                show_alert=True,
            )

    except Exception as e:
        return await callback.answer("⚠️ Ошибка при отмене брони", show_alert=True)
