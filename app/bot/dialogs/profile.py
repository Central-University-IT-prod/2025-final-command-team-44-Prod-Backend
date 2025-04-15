from aiogram import F, Router, types
from aiogram.types import ContentType, Message

from app.bot.settings import emoji
from app.services import BookingService, UserService

router_profile = Router()


@router_profile.message(F.text == (emoji["profile"] + "Профиль"))
async def handle_profile(message: Message):
    service: UserService = UserService()
    profile = await service.get_by_id(message.chat.id)
    if profile is None:
        return await message.answer("⚠️ Профиль не найден")

    service_booking: BookingService = BookingService()

    user_bookings = await service_booking.get_user_bookings(user_id=profile.id)

    msg_bookings = ""
    for i, booking in enumerate(user_bookings):
        msg_bookings += f"""
{i + 1}) <code>{booking.table_name}</code>
<b>Дата:</b> <code>{booking.time_start.strftime("%d.%m.%Y %H:%M")} - {booking.time_end.strftime("%d.%m.%Y %H:%M")}</code>
<b>Код:</b> <code>{booking.code}</code>\n
        """

    text = text = f"""
<b>📄 Профиль</b>
<b>Телеграм ID:</b> <code>{profile.id}</code>
<b>Количество броней:</b> {len(user_bookings)}
<blockquote expandable>{msg_bookings} </blockquote>
    """
    await message.answer(text=text, parse_mode="HTML")


@router_profile.message(F.content_type == ContentType.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    if message.contact.user_id != message.from_user.id:
        return await message.answer("⚠️ Необходимо отправить свой номер телефона!")

    phone_number = contact.phone_number

    service: UserService = UserService()

    try:
        await service.repo.update(message.chat.id, phone=phone_number)
        await message.answer(
            f"📞 Ваш номер телефона {phone_number} был успешно привязан!"
        )
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при сохранении телефона. Пожалуйста, попробуйте еще раз."
        )
