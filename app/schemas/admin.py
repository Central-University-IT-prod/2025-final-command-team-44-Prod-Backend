from pydantic import constr

from ._base import BaseModel, RequestModel


class AdminSignUp(RequestModel):
    login: constr(max_length=120)  # type: ignore
    password: constr(min_length=4, max_length=100)  # type: ignore


class AdminSignIn(RequestModel):
    login: constr(max_length=120)  # type: ignore
    password: constr(min_length=4, max_length=100)  # type: ignore


class AdminSignInResponse(BaseModel):
    token: str


class AdminMe(BaseModel):
    login: str
