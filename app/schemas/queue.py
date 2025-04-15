from typing import Optional

from app.schemas._base import Date
from pydantic import BaseModel, conint

from app.schemas.location import LocationInfo


class JoinQueue(BaseModel):
    date: Optional[Date] = None
    hours: conint(ge=1, le=12)  # type: ignore

class QueueReponse(BaseModel):
    id: str
    date: Optional[Date] = None
    hours: int
    location: LocationInfo