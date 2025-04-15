from uuid import UUID

from app.infra.repository.admin import AdminRepository


class AdminService:
    def __init__(self):
        self.repo = AdminRepository()

    async def get_by_id(self, admin_id: UUID):
        return await self.repo.get(admin_id)

    async def create_admin(self, **admin_data: dict):
        return await self.repo.create(**admin_data)
