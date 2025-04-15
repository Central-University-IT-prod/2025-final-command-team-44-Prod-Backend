from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from app.api.dependencies import CurrentAdmin, get_admin_location
from app.infra.database.models import Location
from app.schemas.booking import BookingAdminResponse, UserBookingForAdmin
from app.schemas.location import *
from app.services.booking import BookingService
from app.services.location import LocationService

router = APIRouter(prefix="/location")


@router.get(
    "/all",
    summary="Получение своих локаций админом",
    response_model=List[LocationInfo],
    tags=["Управление локациями"],
)
async def get_all_admin_locations(
    admin: CurrentAdmin, service: LocationService = Depends(LocationService)
):
    locations = await service.repo.find(admin_id=admin.id)
    return [l.to_dict() for l in locations]


@router.get(
    "/{location_id}",
    summary="Получение локации по ID админом",
    response_model=LocationResponse,
    tags=["Admin Location"],
)
async def get_location(location: Location = Depends(get_admin_location)):
    return LocationResponse(**location.to_dict(), svg=location.svg)


@router.post(
    "",
    summary="Создание локации админом",
    status_code=201,
    response_model=LocationResponse,
    tags=["Admin Location"],
)
async def create_location(
    data: CreateLocation,
    admin: CurrentAdmin,
    service: LocationService = Depends(LocationService),
):
    location = await service.create(
        name=data.name, address=data.address, admin_id=admin.id
    )
    return LocationResponse(**location.to_dict(), svg=location.svg)


@router.put(
    "/{location_id}",
    summary="Обновление локаций админом",
    response_model=LocationResponse,
    tags=["Admin Location"],
)
async def update_location(
    data: UpdateLocation,
    location: Location = Depends(get_admin_location),
    service: LocationService = Depends(LocationService),
):
    if data.open_hour > data.close_hour:
        raise HTTPException(
            status_code=400,
            detail="Час открытия не может быть больше, чем час закрытия",
        )

    location = await service.update(
        id=location.id,
        name=data.name,
        address=data.address,
        open_hour=data.open_hour,
        close_hour=data.close_hour,
    )
    return LocationResponse(**location.to_dict(), svg=location.svg)


@router.put(
    "/{location_id}/svg",
    summary="Загрузка схемы зала админом",
    response_model=LocationResponse,
    tags=["Admin Location"],
)
async def put_svg(
    file: UploadFile,
    location: Location = Depends(get_admin_location),
    service: LocationService = Depends(LocationService),
):
    if not "svg" in file.content_type:
        raise HTTPException(status_code=400, detail="Передан недопустимый формат файла")
    r = await service.set_svg(location_id=location.id, svg=await file.read())

    return LocationResponse(**r.to_dict(), svg=r.svg)


@router.get(
    "/{location_id}/bookings",
    summary="Получить все брони в локации",
    response_model=List[BookingAdminResponse],
    tags=["Admin Location"],
)
async def bookings_location_admin(
    admin: CurrentAdmin,
    location: Location = Depends(get_admin_location),
    booking_service: BookingService = Depends(BookingService),
):
    return [
        BookingAdminResponse(
            id=entry.id,
            location_id=entry.table.location.id,
            code=entry.code,
            table_id=entry.table.id,
            table_name=entry.table.table_name,
            time_start=entry.time_start,
            time_end=entry.time_end,
            comment=entry.comment,
            features=entry.features,
            people_amount=entry.people_amount,
            users=[
                UserBookingForAdmin(
                    id=bookuser.id,
                    first_name=bookuser.user.first_name,
                    username=bookuser.user.username,
                    user_id=bookuser.user.id,
                    status=bookuser.status,
                )
                for bookuser in entry.users
            ],
        )
        for entry in await booking_service.get_location_bookings(location.id, admin.id)
    ]


@router.delete(
    "/{location_id}",
    summary="Удаление локации админом",
    tags=["Admin Location"],
)
async def delete_location(
    location: Location = Depends(get_admin_location),
    servce: LocationService = Depends(LocationService),
):
    await servce.delete(location_id=location.id, admin_id=location.admin_id)
    return Response(status_code=204)
