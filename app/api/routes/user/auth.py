import json

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import CurrentUser
from app.schemas import UserMe, UserSignInResponse, UserTelegramLogin
from app.services import UserService
from app.utils import telegram
from app.utils.security import create_jwt_token

router = APIRouter(tags=["Аутентификация пользователей"])


@router.get(
    "/me",
    response_model=UserMe,
    summary="Получение профиля пользователем",
    status_code=200,
)
async def user_me(user: CurrentUser):
    return UserMe(
        telegram_id=user.id, first_name=user.first_name, username=user.username
    )


@router.post(
    "/auth/telegram",
    summary="Аутентификация пользователя по InitData",
    response_model=UserSignInResponse,
    status_code=200,
)
async def telegram_auth(
    data: UserTelegramLogin, service: UserService = Depends(UserService)
):
    parsed_data = telegram.validate_init_data(data.init_data)
    if not parsed_data:
        raise HTTPException(status_code=401, detail="Невалидная init data.")

    user_info: dict = json.loads(parsed_data["user"])

    user_id = int(user_info["id"])
    username = user_info.get("username")
    first_name = user_info.get("first_name")
    user = await service.get_or_create(
        user_id, first_name=first_name, username=username
    )

    auth_token = create_jwt_token(data={"user_id": user.id})
    return dict(token=auth_token)
