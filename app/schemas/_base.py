import re
from collections import namedtuple
from datetime import datetime
from enum import Enum
from typing import ClassVar, Self, Type, get_type_hints

from app.config import TIMEZONE
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


def get_cls_fields_type(cls: BaseModel):
    annotations = get_type_hints(cls)

    data = {k: v.annotation for k, v in cls.model_fields.items()}

    for k, v in annotations.items():
        if v.__dict__.get("_name") == "Optional":
            class_ = v.__dict__.get("__args__", [str])[0]
        else:
            class_ = v
        data[k] = class_

    return namedtuple("fields", data.keys())(**data)


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: ClassVar[Self]

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        _fields = get_cls_fields_type(cls)
        setattr(cls, "fields", _fields)


class IgnoreCaseEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: str):
        normalized_value = value.lower()
        for member in cls:
            if str(member.value).lower() == normalized_value:
                return member


class CustomField:
    type: Type

    @classmethod
    def validation(cls, value):
        return value

    @classmethod
    def validate(cls, value, strict=True):
        if strict:
            return cls.validation(value)
        try:
            return cls.validation(value)
        except Exception:
            ...

    def __new__(cls, value):
        return cls.validate(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(cls.type))


def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


class Email(CustomField):
    type = str

    @classmethod
    def validation(cls, value):
        if not 8 <= len(value) <= 120:
            raise ValueError("Почта должна быть от 8 до 120 символов.")

        if not validate_email(value):
            raise ValueError("Введите Ваш настоящий email.")

        return value


class Date(CustomField):
    type = datetime

    @classmethod
    def validation(cls, value: datetime):
        if value < datetime.now(TIMEZONE):
            raise ValueError("Вы не можете указать время раньше текущего.")

        return value.replace(minute=0, second=0, microsecond=0)
