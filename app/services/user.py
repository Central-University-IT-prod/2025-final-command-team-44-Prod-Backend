from app.infra.repository.user import UserRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def create_user(self, **user_data):
        return await self.repo.create(**user_data)

    async def get_by_id(self, user_id: int):
        return await self.repo.get(user_id)

    async def get_or_create(self, user_id: int, first_name: str, username: str):
        user = await self.get_by_id(user_id)
        if not user:
            user = await self.create_user(
                **dict(
                    id=user_id,
                    first_name=first_name,
                    username=username
                )
            )
        return user
