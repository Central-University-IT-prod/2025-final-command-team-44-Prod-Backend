from datetime import datetime
from typing import List, Optional

from app.schemas._base import Date, RequestModel
from pydantic import BaseModel, Field, conint, constr


class UpdateBooking(RequestModel):
    time_start: Date = Field(description="Дата начала, минуты и секунды обрезаются")
    hours: conint(ge=1, le=12)  # type: ignore
    features: List[constr(max_length=520)] = None # type: ignore
    comment: Optional[constr(max_length=520)] = None  # type: ignore
    people_amount: int


class CreateBooking(RequestModel):
    time_start: Date = Field(description="Дата начала, минуты и секунды обрезаются")
    hours: conint(ge=1, le=12)  # type: ignore
    features: List[constr(max_length=520)] = None  # type: ignore
    comment: Optional[constr(max_length=520)] = None  # type: ignore
    people_amount: int = 1

class CreateBookingAdmin(RequestModel):
    time_start: Date = Field(description="Дата начала, минуты и секунды обрезаются")
    hours: conint(ge=1, le=12)  # type: ignore
    features: List[constr(max_length=520)] = None  # type: ignore
    comment: Optional[constr(max_length=520)] = None  # type: ignore
    people_amount: int = 1
    phone_number: str

class BookingResponse(BaseModel):
    id: str
    location_id: str
    code: str
    table_id: str
    table_name: str
    comment: Optional[str] = None
    features: Optional[List[str]] = None
    people_amount: int


class UserBookingForAdmin(BaseModel):
    id: str
    first_name: str
    username: Optional[str] = None
    user_id: int
    status: str

class BookingAdminResponse(BaseModel):
    id: str
    location_id: str
    code: str
    table_id: str
    table_name: str
    time_start: datetime
    time_end: datetime
    comment: Optional[str] = None
    features: Optional[List[str]] = None
    people_amount: int
    users: List[UserBookingForAdmin]

class JoinGroup(RequestModel):
    booking_id: str = Field(
        ..., description="Айдишник брони к которой хотим присоединиться"
    )


class MyGroupResponse(BaseModel):
    booking_id: str = Field(..., description="Айдишник брони")

    table_id: str = Field(..., description="Айдишник места")
    table_name: str = Field(..., description="Название места")

    time_start: datetime = Field(..., description="Время начала брони")
    time_end: datetime = Field(..., description="Время окончания брони")
    code: str = Field(..., description="Код для входа")
    status: str = Field(..., description="Статус пользователя в этой брони")
    features: Optional[List[str]] = Field(..., description="Утилиты для пользователя")
    comment: Optional[str] = Field(..., description="Комментарий пользователя")

    people_amount: int = Field(..., description="Количество пользователей в брони")

    invite_url: Optional[str]


class GroupMembers(RequestModel):
    user_id: int = Field(..., description="Айдишник участника")
    username: Optional[str] = Field(..., description="Имя пользователя участника")
    first_name: str = Field(..., description="Имя участника")

    status: str = Field(..., description="Статус участника")


class GetBusyTables(RequestModel):
    time_start: Date = Field(description="Дата начала, минуты и секунды обрезаются")
    hours: int
