from app.schemas._base import CustomField, RequestModel
from pydantic import BaseModel, conint, constr



class CreateLocation(RequestModel):
    name: constr(max_length=255)  # type: ignore
    address: constr(max_length=255)  # type: ignore


class UpdateLocation(RequestModel):
    name: constr(max_length=255)  # type: ignore
    address: constr(max_length=255)  # type: ignore
    open_hour: conint(ge=0, le=24)  # type: ignore
    close_hour: conint(ge=0, le=24)  # type: ignore


class LocationInfo(BaseModel):
    id: str
    name: str
    address: str
    open_hour: int
    close_hour: int


class LocationResponse(BaseModel):
    id: str
    name: str
    address: str
    svg: str
    open_hour: int
    close_hour: int