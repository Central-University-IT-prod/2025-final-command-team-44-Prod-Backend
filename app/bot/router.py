from aiogram import F, Router
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram.types import ErrorEvent
from aiogram_dialog.api.exceptions import (OutdatedIntent, UnknownIntent,
                                           UnknownState)
from app.bot.settings import emoji
from app.bot.settings import keyboards as kb
from app.bot.settings import messages
from app.bot.utils import (DialogManager, Message, UserMiddleware,
                           extract_payload)
from app.exceptions import ServiceException

router = Router()

router.message.middleware(UserMiddleware())


@router.message(CommandStart())
@router.message(F.text == messages["start_btn"])
async def start(message: Message, dialog_manager: DialogManager):
    payload = await extract_payload(message.text)

    if payload and "booking" in payload:
        booking_id = payload.split("_")[-1]

        user_booking = await message.bot.booking.join(
            booking_id=booking_id, user_id=message.from_user.id, status="member"
        )

        return await message.answer(
            messages["joined"].format(user_booking.booking.code), reply_markup=kb.details(path="/bookings")
        )

    await message.answer(emoji["wave"], reply_markup=kb.main)
    await message.answer(messages["start"], reply_markup=kb.webapp)


@router.errors(ExceptionTypeFilter(UnknownState, UnknownIntent, OutdatedIntent))
async def handle_states_exception(event: ErrorEvent, dialog_manager: DialogManager):
    update = event.update.message or event.update.callback_query
    user = update.from_user.id

    try:
        await update.bot.send_message(
            chat_id=user, text=messages["start"], reply_markup=kb.main
        )
    except:
        pass


@router.errors(F.update.message.as_("message"), ExceptionTypeFilter(ServiceException))
async def handle_service_exception(event: ErrorEvent, message: Message):
    exception: ServiceException = event.exception
    await message.answer(text=exception.detail)


#@router.error(F.update.message.as_("message"))
async def handle_exception(event: ErrorEvent, message: Message):
    detail = event.exception.__dict__.get("detail")
    if detail:
        return await message.answer(text=detail)
    await message.answer(text=str(event.exception))
