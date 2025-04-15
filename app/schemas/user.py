from typing import Optional
from ._base import BaseModel, RequestModel


class UserSignInResponse(BaseModel):
    token: str


class UserMe(BaseModel):
    telegram_id: int
    first_name: str
    username: Optional[str] = None


class UserTelegramLogin(RequestModel):
    init_data: str
