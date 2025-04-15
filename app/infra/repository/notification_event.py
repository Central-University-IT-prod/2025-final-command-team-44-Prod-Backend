from app.infra.database.models import NotificationEvent
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository


class NotificationRepository(BaseRepository[NotificationEvent]):
    model = NotificationEvent
    session = async_session
