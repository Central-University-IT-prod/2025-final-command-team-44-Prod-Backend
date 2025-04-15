from typing import List, Optional

from app.schemas._base import RequestModel
from pydantic import BaseModel


class TablePatch(RequestModel):
    features: Optional[List[str]] = None
    max_people_amount: int


class TableResponse(BaseModel):
    id: str
    table_name: str
    max_people_amount: int
    location_id: str
    features: Optional[List[str]] = None
