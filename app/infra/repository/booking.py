from app.infra.database.models import Booking, BookingUser, Location, Table, User
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository
from sqlalchemy import Date, cast, func, select


class BookingRepository(BaseRepository[Booking]):
    model = Booking
    session = async_session

    async def create_booking(self, table_id, time_start, time_end, features, comment, people_amount, location_id, table_name, user_id):
        async with self.session() as session:
            query = (
                select(BookingUser)
                .join(Booking)
                .join(Table)
                .filter(
                    Location.id == location_id, 
                    BookingUser.user_id == user_id,
                    cast(Booking.time_start, Date) == time_start.date()
                )
            )
            result = await session.execute(query)
            existing_bookings = result.scalars().all()
            if existing_bookings:
                return 400
            
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
            existing_bookings = result.scalars().all()
            if existing_bookings:
                return 409
            
            item = self.model(**dict(
                table_id=table_id,
                time_start=time_start,
                time_end=time_end,
                features=features,
                comment=comment,
                people_amount=people_amount,
            ))
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item


    async def get_user_booking_by_user_id(self, user_id: int):
        async with self.session() as session:
            res = await session.execute(
                select(
                    Booking.id,
                    Table.id.label("table_id"),
                    Table.table_name,
                    Booking.time_start,
                    Booking.time_end,
                    Booking.features,
                    Booking.comment,
                    Booking.code,
                    Booking.people_amount,
                    BookingUser.status,
                )
                .join(BookingUser)
                .join(Table)
                .where(BookingUser.user_id == user_id)
                .where(Booking.time_end > func.now())
            )
            return res.mappings().fetchall()

    async def get_booking_members(self, booking_id: str):
        async with self.session() as session:
            res = await session.execute(
                select(
                    User.username,
                    User.first_name,
                    BookingUser.user_id,
                    BookingUser.status,
                )
                .join(Booking)
                .join(User)
                .where(Booking.id == booking_id)
            )

            return res.mappings().fetchall()

class BookingUserRepository(BaseRepository[BookingUser]):
    model = BookingUser
    session = async_session
