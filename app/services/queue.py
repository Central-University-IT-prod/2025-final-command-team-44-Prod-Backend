from app.infra.database.models import *
from app.infra.repository.queue import QueueRepository


class QueueService:
    queue = QueueRepository()

    async def add_user(
        self, user_id: int, date: datetime, hours: int, location_id: str
    ):
        await self.queue.create(
            user_id=user_id, date=date, hours=hours, location_id=location_id
        )

    async def get_user_queues_by_day(self, user_id: int, data):
        return await self.queue.get_user_queues_by_day(user_id, data)

    async def get_location_queues_by_day(self, location_id: str, data: datetime):
        return await self.queue.get_location_queues_by_day(location_id, data)