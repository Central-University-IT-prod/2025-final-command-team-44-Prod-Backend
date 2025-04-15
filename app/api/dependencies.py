from typing import Annotated

from app.config import TEST_MODE
from app.infra.database.models import *
from app.services import AdminService, BookingService, UserService
from app.services.location import LocationService
from app.utils.security import verify_jwt_token
from fastapi import Depends, HTTPException, Query, WebSocketException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

auth_scheme = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    service: UserService = Depends(UserService),
):
    if TEST_MODE:
        decoded_data = {"user_id": token.credentials}
    else:
        decoded_data = verify_jwt_token(token.credentials)
        if not decoded_data:
            raise HTTPException(
                status_code=401, detail="Пользователь не авторизован.")

    try:
        user = await service.get_by_id(int(decoded_data["user_id"]))
        if not user:
            raise ValueError
    except:
        raise HTTPException(
            status_code=401, detail="Пользователь не авторизован.")
    return user


async def get_current_ws_user(
    token: Annotated[str | None, Query()] = None,
    service: UserService = Depends(UserService),
):
    if not token:
        raise WebSocketException(code=1008)

    decoded_data = verify_jwt_token(token)
    if not decoded_data:
        raise WebSocketException(code=1008)

    try:
        user = await service.get_by_id(int(decoded_data["user_id"]))
        if not user:
            raise ValueError
    except:
        raise WebSocketException(code=1008)
    return user


async def get_current_admin(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    service: AdminService = Depends(AdminService),
):
    decoded_data = verify_jwt_token(token.credentials)
    if not decoded_data:
        raise HTTPException(status_code=401, detail="Админ не авторизован.")

    try:
        admin = await service.get_by_id(decoded_data["admin_id"])
        if not admin:
            raise ValueError
    except:
        raise HTTPException(status_code=401, detail="Админ не авторизован.")
    return admin


async def get_exists_booking(
    booking_id: str, service: BookingService = Depends(BookingService)
):
    booking = await service.repo.get(booking_id)

    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    return booking


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]
CurrentWsUser = Annotated[User, Depends(get_current_ws_user)]


async def get_exist_location(
    location_id: str, service: LocationService = Depends(LocationService)
):
    location = await service.repo.get(location_id)

    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")

    return location


async def get_admin_location(
    location_id: str,
    admin: CurrentAdmin,
    service: LocationService = Depends(LocationService),
):
    location = await service.get(location_id, admin_id=admin.id)
    return location


async def get_admin_location_table(
    table_id: str,
    location: Location = Depends(get_admin_location),
    service: LocationService = Depends(LocationService),
):
    table = await service.tables.find_one(id=table_id, location_id=location.id)

    if not table:
        raise HTTPException(status_code=404, detail="Место не найдено")

    return table

async def get_admin_location_table_name(
    table_name: str,
    location: Location = Depends(get_admin_location),
    service: LocationService = Depends(LocationService),
):
    table = await service.tables.find_one(table_name=table_name, location_id=location.id)

    if not table:
        raise HTTPException(status_code=404, detail="Место не найдено")

    return table


async def get_exist_booking(
    booking_id: str, service: BookingService = Depends(BookingService)
):
    booking = await service.repo.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено.")
    return booking


async def get_user_booking(
    user: CurrentUser,
    booking: Booking = Depends(get_exist_booking),
    service: BookingService = Depends(BookingService),
):
    book_member = await service.get_user_booking_by_user_id(
        booking_id=booking.id, user_id=user.id
    )
    if not book_member or book_member.status != BookingUserStatusEnum.creator:
        raise HTTPException(
            status_code=403, detail="Вы не имеете доступ к редактированию бронирования."
        )
    return book_member.booking
