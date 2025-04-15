from datetime import date, datetime

from app.infra.database.models import Booking, Table, Location
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository
from sqlalchemy import Date, cast, select


class TableRepository(BaseRepository[Table]):
    model = Table
    session = async_session

    async def get_bookings(self, location_id, table_name, date: date):
        async with self.session() as session:
            results = await session.scalars(
                select(Booking)
                .join(Table)
                .filter(
                    cast(Booking.time_start, Date) == cast(date, Date),
                    Table.location_id == location_id,
                    Table.table_name == table_name,
                )
            )
            return results.all()
        
    async def get_location_bookings(self, location_id: str, admin_id: str):
        async with self.session() as session:
            results = await session.scalars(
                select(Booking)
                .join(Table)
                .join(Location)
                .filter(
                    Table.location_id == location_id,
                    Location.admin_id == admin_id
                )
            )
            return list(results.all())

    async def get_table_bookings(self, table_id: str, admin_id: str):
        async with self.session() as session:
            results = await session.scalars(
                select(Booking)
                .join(Table)
                .filter(
                    Table.id == table_id,
                    Table.location.has(admin_id == admin_id),
                )
            )
            return results.all()

    async def is_table_free(
        self,
        table_name: str,
        location_id: str,
        time_start: datetime,
        time_end: datetime,
        ignore: str = None,
    ) -> bool:
        async with self.session() as session:
            query = (
                select(Booking)
                .join(Table)
                .filter(
                    Table.location_id == location_id,
                    Table.table_name == table_name,
                )
                .where(
                    (Booking.time_start < time_end) &
                    (Booking.time_end > time_start)
                )
            )
            result = await session.execute(query)
            bookings = result.scalars().all()
            if ignore:
                bookings = [booking for booking in bookings if booking.id != ignore]
            return len(bookings) == 0
        
    async def get_count_bookings(
        self,
        location_id: str,
        time_start: datetime,
        time_end: datetime,
        ignore: str = None,
    ) -> bool:
        async with self.session() as session:
            query = (
                select(Booking)
                .join(Table)
                .filter(
                    Table.location_id == location_id
                )
                .where(
                    (Booking.time_start < time_end) &
                    (Booking.time_end > time_start)
                )
            )
            result = await session.execute(query)
            bookings = result.scalars().all()
            if ignore:
                bookings = [booking for booking in bookings if booking.id != ignore]
            return bookings

    async def get_total_tables(
        self,
        location_id: str
    ) -> int:
        async with self.session() as session:
            query = select(Table).filter(Table.location_id == location_id, Table.max_people_amount == 1)
            result = await session.execute(query)
            tables = result.scalars().all()
            return tables


    async def get_booking_timeline(
        self,
        location_id,
        table_name,
        date: date,
        is_two_days: bool = False,
        ignore: str = None,
    ):
        timeline = [0] * (24 if not is_two_days else 48)

        for i in range(0, 2):
            new_date = date.replace(day=date.day + i)
            bookings = await self.get_bookings(
                location_id=location_id, table_name=table_name, date=new_date
            )

            for book in bookings:
                if book.id == ignore:
                    continue
                time_start: datetime = book.time_start
                time_end: datetime = book.time_end

                for j in range(time_start.hour, time_end.hour):
                    timeline[24 * i + j] = 1

        return timeline
    
    async def get_bookings_timelines(
        self, location_id: str, date: datetime, is_two_days: bool = False
    ):
        tables = await self.find(location_id=location_id)

        timelines = []
        for i in range(len(tables)):
            table = tables[i]
            timeline = await self.get_booking_timeline(
                location_id=location_id,
                table_name=table.table_name,
                date=date,
                is_two_days=is_two_days,
            )
            timelines.append(timeline)

        return timelines
