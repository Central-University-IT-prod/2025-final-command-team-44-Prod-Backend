from app.infra.database.models import Location
from app.infra.database.session import async_session
from app.infra.repository._base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    model = Location
    session = async_session
