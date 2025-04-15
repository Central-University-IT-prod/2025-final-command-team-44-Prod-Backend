from aiogram import Router, types
from aiogram.filters import Command

from app.services.user import UserService

router_get_jwt = Router()


@router_get_jwt.message(Command("get_jwt"))
async def get_jwt(message: types.Message):
    from app.utils.security import create_jwt_token

    service: UserService = UserService()

    user_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name

    user = await service.get_or_create(
        user_id=user_id, first_name=first_name, username=username
    )

    token = create_jwt_token(data={"user_id": user.id})

    await message.answer(f"Твой <b>JWT</b> для тестирования:\n\n<code>{token}</code>")
