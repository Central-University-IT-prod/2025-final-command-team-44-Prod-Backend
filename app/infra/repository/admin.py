from app.infra.database.models import Admin
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    model = Admin
    session = async_session
