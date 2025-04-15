from typing import Generic, List, Type, TypeVar

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

M = TypeVar("M")


class BaseRepository(Generic[M]):
    model: Type[M]
    session: async_sessionmaker[AsyncSession]

    async def create(self, **data) -> M:
        async with self.session() as session:
            item = self.model(**data)
            session.add(item)

            await session.commit()
            await session.refresh(item)
            return item

    async def get(self, id, options=None) -> M:
        async with self.session() as session:
            # if options is not None:
            #     return await session.scalar(
            #         select(self.model).options(*options).where(self.model.id == id)
            #     )

            return await session.scalar(select(self.model).where(self.model.id == id))

    async def get_or_create(self, id, **kwargs):
        item = await self.get(id)
        if not item:
            return await self.create(id=id, **kwargs)
        return item

    async def find(self, limit=None, offset=None, **conditions) -> List[M]:
        async with self.session() as session:
            items = await session.scalars(
                select(self.model)
                .filter_by(**conditions)
                .limit(limit)
                .offset(offset)
                .order_by(desc(self.model.created_at))
            )
            return items.all()

    async def find_one(self, **conditions) -> M:
        results = await self.find(limit=1, **conditions)

        if results:
            return results[0]

    async def get_all(self, limit=None, offset=None) -> List[M]:
        async with self.session() as session:
            items = await session.scalars(
                select(self.model)
                .limit(limit)
                .offset(offset)
                .order_by(desc(self.model.created_at))
            )
            return items.all()

    async def update(self, id, **updates) -> M:
        async with self.session() as session:
            item = await session.scalar(select(self.model).where(self.model.id == id))

            for k, v in updates.items():
                setattr(item, k, v)

            await session.commit()
            await session.refresh(item)

            return item

    async def delete(self, id):
        async with self.session() as session:
            await session.execute(delete(self.model).where(self.model.id == id))
            await session.commit()
