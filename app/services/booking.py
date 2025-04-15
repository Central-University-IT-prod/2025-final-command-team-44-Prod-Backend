from datetime import date, datetime, timedelta

from app.exceptions import ServiceException
from app.infra.repository import (BookingRepository, BookingUserRepository,
                                  TableRepository, UserRepository)
from app.schemas.booking import MyGroupResponse


class BookingService:
    def __init__(self):
        self.repo = BookingRepository()
        self.users = UserRepository()
        self.booking_users = BookingUserRepository()
        self.tables = TableRepository()

    async def drop_location_bookingd(self, location_id: str):
        ...

    async def create_booking(self, table_id, time_start, time_end, features, comment, people_amount, location_id, table_name, user_id):
        booking = await self.repo.create_booking(table_id, time_start, time_end, features, comment, people_amount, location_id, table_name, user_id)
        if booking == 409:
            raise ServiceException(status_code=409, detail="На это время уже есть бронь.")
        elif booking == 400:
            raise ServiceException(status_code=400, detail="У вас уже есть забронированное место в этой локации.")
        await self.join(user_id=user_id, booking_id=booking.id, status="creator")
        return booking

    async def get_table_bookings(self, table_id, date: date):
        table = await self.tables.get(table_id)

        return await self.tables.get_bookings(
            location_id=table.location_id, table_name=table.table_name, date=date
        )
    
    async def get_location_bookings(self, location_id: str, admin_id: str):
        return await self.tables.get_location_bookings(
            location_id=location_id, admin_id=admin_id
        )

    async def is_booking_avalale(
        self,
        table_name: str,
        location_id: str,
        time_start: datetime,
        time_end: datetime,
        ignore: str = None,
    ) -> bool:
        is_table_free = await self.tables.is_table_free(
            table_name=table_name,
            location_id=location_id,
            time_start=time_start,
            time_end=time_end,
            ignore=ignore,
        )

        return is_table_free 

    async def join(self, booking_id: str, user_id: int, status: str):
        user = await self.users.get(id=user_id)

        if not user:
            raise ServiceException(status_code=404, detail="Пользователь не найден")

        booking = await self.repo.get(id=booking_id)

        if not booking:
            raise ServiceException(status_code=404, detail="Бронь не найдена")
        

        booking_user = await self.booking_users.find_one(
            user_id=user_id, booking_id=booking_id
        )

        if not booking_user:
            members = await self.repo.get_booking_members(booking_id=booking_id)
            print(members, booking.people_amount)
            if len(members) >= booking.people_amount:
                raise ServiceException(
                    status_code=409,
                    detail="В этой брони уже максимальное количество пользователей",
                )
            
            booking_user = await self.booking_users.create(
                user_id=user_id, booking_id=booking_id, status=status
            )

        return booking_user

    async def get_user_bookings(self, user_id: int):
        from app.bot.utils import create_ref_link

        user = await self.users.get(id=user_id)

        if not user:
            raise ServiceException(status_code=404, detail="Пользователь не найден")

        bookings = await self.repo.get_user_booking_by_user_id(user_id=user.id)

        response = []
        for b in bookings:
            invite_url = None
            if b["status"].value == "creator":
                invite_url = await create_ref_link(payload=f"booking_{b['id']}")

            resp = MyGroupResponse(
                booking_id=b["id"],
                table_id=b["table_id"],
                features=b['features'],
                comment = b['comment'],
                table_name=b["table_name"],
                time_start=b["time_start"],
                time_end=b["time_end"],
                people_amount=b["people_amount"],
                code=b["code"],
                status=b["status"].value,
                invite_url=invite_url,
            )
            response.append(resp)
        return response

    async def get_user_booking_by_user_id(self, booking_id: str, user_id: int):
        return await self.booking_users.find_one(user_id=user_id, booking_id=booking_id)
    
    async def get_booking_members(self, booking_id):
        members = await self.repo.get_booking_members(booking_id=booking_id)
        return [dict(**m, status=m["status"].value) for m in members]

    async def get_busy_table_names(self, location_id, time_start: datetime, hours: int):
        tables = await self.tables.find(location_id=location_id)

        busy = []
        for table in tables:
            time_end = time_start + timedelta(hours=hours)

            available = await self.is_booking_avalale(
                table_name=table.table_name,
                location_id=table.location_id,
                time_start=time_start,
                time_end=time_end,
            )

            if not available:
                busy.append(table.table_name)
        return busy
