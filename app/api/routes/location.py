from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_exist_location
from app.infra.database.models import Location
from app.schemas import GetBusyTables, LocationInfo, LocationResponse, TableResponse
from app.services import BookingService, LocationService

router = APIRouter(prefix="/location", tags=["Локации"])


@router.get("/all", summary="Получение всех локаций", response_model=List[LocationInfo])
async def get_all_locations(
    service: LocationService = Depends(LocationService),
    limit: int = Query(10, alias="limit", ge=1),
    offset: int = Query(0, alias="offset", ge=0),
):
    locations = await service.repo.find(limit=limit, offset=offset)
    return [l.to_dict() for l in locations]


@router.get(
    "/{location_id}", summary="Получение локации по ID", response_model=LocationResponse
)
async def get_location(location: Location = Depends(get_exist_location)):
    return LocationResponse(**location.to_dict(), svg=location.svg)


@router.get(
    "/{location_id}/tables",
    summary="Получение мест локации",
    response_model=List[TableResponse],
)
async def get_location_tables(
    location: Location = Depends(get_exist_location),
    service: LocationService = Depends(LocationService),
):
    tables = await service.get_location_tables(location_id=location.id)

    return [
        TableResponse(
            id=table.id,
            table_name=table.table_name,
            location_id=table.location_id,
            features=table.features,
            max_people_amount=table.max_people_amount,
        )
        for table in tables
    ]


@router.post(
    "/{location_id}/bookings",
    summary="Получение всех занятых мест в промежутке времени",
    response_model=List[str],
)
async def get_location_bookings(
    data: GetBusyTables,
    location: Location = Depends(get_exist_location),
    booking_service: BookingService = Depends(BookingService),
):
    return await booking_service.get_busy_table_names(
        location_id=location.id, time_start=data.time_start, hours=data.hours
    )
