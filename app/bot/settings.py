from aiogram.types import InlineKeyboardButton, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from app.config import HOST

emoji = {
    "id": "\U0001f194",
    "calendar": "\U0001f4c5 ",
    "stats": "\U0001f4ca ",
    "search": "\U0001f50d ",
    "nums": "\U0001f522 ",
    "clock": "\U0001f553 ",
    "globe": "\U0001f30d ",
    "restart": "\U0001f504 ",
    "gender": "\U0001f465 ",
    "profile": "\U0001f464 ",
    "like": "\U0001f44d ",
    "pencil": "\u270f ",
    "success": "\u2705 ",
    "internet": "\U0001f310 ",
    "email": "\U0001f4e8 ",
    "wave": "\U0001f44b ",
    "info": "\u2139 ",
    "lock": "\U0001f512 ",
    "unlock": "\U0001f513 ",
    "text": "\U0001f524 ",
    "back": "\U0001f519 ",
    "robot": "\U0001f916 ",
    "warning": "\u26a0 ",
    "sand": "\u23f3 ",
    "star": "\U0001f4ab",
    "upload": "\U0001f4e5 ",
}

messages = {
    "profile_btn": emoji["profile"] + "Профиль",
    "faq_btn": emoji["info"] + "FAQ",
    "start_btn": emoji['calendar'] + "Забронировать коворкинг",
    "start": emoji["wave"] + "<b>Приветствуем вас в нашем Телеграм-боте!</b>\n",
    "joined": emoji["success"]
    + "<b>Вы успешно присоединились к встрече в коворкинге</b>\nВаш код: <b>{}</b>",
}


class keyboards:
    main = (
        ReplyKeyboardBuilder()
        .row(
            KeyboardButton(text=messages["start_btn"]),
            KeyboardButton(text=messages["profile_btn"]),
        )
        .row(
            KeyboardButton(text="📞 Привязать номер телефона", request_contact=True),
            #KeyboardButton(text=messages["faq_btn"]),
        )
        .as_markup(resize_keyboard=True)
    )
    webapp = (
        InlineKeyboardBuilder()
        .row(InlineKeyboardButton(text="Перейти к бронированию", web_app=WebAppInfo(url=HOST)))
        .as_markup()
    )

    def details(path: str):
        return (
            InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="Подробнее 👀", web_app=WebAppInfo(url=HOST + path)
                )
            )
            .as_markup()
        )
