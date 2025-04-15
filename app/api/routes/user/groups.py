from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, get_exists_booking
from app.infra.database.models import Booking
from app.schemas.booking import GroupMembers, JoinGroup, MyGroupResponse
from app.services.booking import BookingService

router = APIRouter(prefix="/booking", tags=["Пользовательское бронирование"])


@router.post("/join", summary="Присоединение к бронированию", status_code=200)
async def join_booking(
    data: JoinGroup,
    user: CurrentUser,
    service: BookingService = Depends(BookingService),
):
    return await service.join(
        user_id=user.id, booking_id=data.booking_id, status="member"
    )


@router.get(
    "/my",
    summary="Получение всех бронирований",
    status_code=200,
    response_model=List[MyGroupResponse],
)
async def get_my_bookings(
    user: CurrentUser, service: BookingService = Depends(BookingService)
):
    return await service.get_user_bookings(user_id=user.id)


@router.get(
    "/members/{booking_id}",
    summary="Получение участников бронирования",
    status_code=200,
    response_model=List[GroupMembers],
)
async def get_booking_members(
    booking: Booking = Depends(get_exists_booking),
    service: BookingService = Depends(BookingService),
):
    return await service.repo.get_booking_members(booking_id=booking.id)
