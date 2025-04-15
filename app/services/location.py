from datetime import datetime
from os import getenv

from app.exceptions import ServiceException
from app.infra.database.models import Location
from app.infra.repository.location import LocationRepository
from app.infra.repository.table import TableRepository
from app.infra.s3.storage import Storage
from app.utils.parse_svg import extract_table_ids

DEFAULT_TABLE_PERSONS = int(getenv('DEFAULT_TABLE_PERSONS', 1))


class LocationService:
    def __init__(self):
        self.repo = LocationRepository()
        self.tables = TableRepository()

    async def create(self, name: str, address: str, admin_id: str) -> Location:
        return await self.repo.create(name=name, address=address, admin_id=admin_id)

    async def update(
        self, id: str, name: str, address: str, open_hour: int, close_hour: int
    ) -> Location:
        return await self.repo.update(
            id=id,
            name=name,
            address=address,
            open_hour=open_hour,
            close_hour=close_hour,
        )

    async def set_svg(self, location_id: str, svg: bytes):
        if not svg:
            return

        location = await self.repo.get(location_id)

        tables = extract_table_ids(svg)

        if not tables:
            raise ServiceException(
                status_code=400, detail='Файл не соответствует требованиям, мы не распознали в нем столы и комнаты')

        for table in await self.tables.find(location_id=location.id):
            await self.tables.delete(id=table.id)

        for table in tables:
            max_people_amount = (
                DEFAULT_TABLE_PERSONS if table.startswith("table") else 5
            )

            t = await self.tables.create(
                table_name=table,
                location_id=location.id,
                max_people_amount=max_people_amount,
            )

        storage = Storage("locations")

        filename = f"{location_id}.svg"
        await storage.delete_file(filename)
        await storage.upload_file(svg, filename)

        return location

    async def get(self, location_id: str, admin_id: str) -> Location:
        location = await self.repo.get(location_id)

        if not location:
            raise ServiceException(
                status_code=404, detail="Локация не найдена")

        if location.admin_id != admin_id:
            raise ServiceException(
                status_code=403, detail="Локация вам не принадлежит")

        return location

    async def delete(self, location_id: str, admin_id: str) -> None:
        location = await self.get(location_id=location_id, admin_id=admin_id)

        await self.repo.delete(location.id)

    async def get_location_tables(self, location_id: str):
        tables = await self.tables.find(location_id=location_id)

        return tables
