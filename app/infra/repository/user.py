from app.infra.database.models import User
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
    session = async_session
