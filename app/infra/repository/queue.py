from app.infra.database.models import Location, QueueUser, User
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository
from sqlalchemy import Date, cast, select, or_


class QueueRepository(BaseRepository[QueueUser]):
    model = QueueUser
    session = async_session

    async def get_user_queues_by_day(self, user_id: int, date):
        async with self.session() as session:
            results = await session.scalars(
                select(QueueUser).join(User).filter(
                    cast(QueueUser.date, Date) == date, QueueUser.user_id == user_id)
            )
            return results.all()

    async def get_user_queues(self, user_id: int):
        async with self.session() as session:
            results = await session.scalars(
                select(QueueUser).join(User).filter(QueueUser.user_id == user_id)
            )
            return results.all()

    async def get_location_queues_by_day(self, location_id: str, date):
        async with self.session() as session:
            results = await session.execute(
                select(QueueUser)
                .join(Location)
                .filter(
                    QueueUser.location_id == location_id,
                    or_(
                        QueueUser.date == None,
                        cast(QueueUser.date, Date) == cast(date, Date)
                    )
                )
                .order_by(QueueUser.created_at.desc())
            )
            return results.scalars().all()
