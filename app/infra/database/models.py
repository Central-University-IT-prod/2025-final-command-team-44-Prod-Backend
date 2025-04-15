import enum
import uuid
from datetime import datetime
from os import getenv
from random import randint
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.utils.security import hash_password

IMAGES_URL = getenv("IMAGES_URL", "http://localhost:8080/images/")


def generate_uuid():
    return str(uuid.uuid4())


def generate_code():
    return str(randint(0, 9999)).zfill(4)


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String, default=generate_uuid, primary_key=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    first_name = mapped_column(String(120), nullable=False)
    username = mapped_column(String(120), nullable=True)
    phone = mapped_column(String(20), nullable=True)

    def __repr__(self):
        return f"{self.id} | {self.username} | {self.first_name} | {self.phone}"


class AdminAuthModel(Base):
    __abstract__ = True

    login = mapped_column(String(120), nullable=False)
    _password = mapped_column("password", String(100), nullable=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = hash_password(value)


class Admin(AdminAuthModel):
    __tablename__ = "admins"

    def __repr__(self):
        return self.login


class Location(Base):
    __tablename__ = "locations"

    name = mapped_column(String(255), nullable=False)
    address = mapped_column(String(255), nullable=False)

    open_hour = mapped_column(Integer, default=0, nullable=False)
    close_hour = mapped_column(Integer, default=24, nullable=False)

    admin_id = mapped_column(
        ForeignKey("admins.id", ondelete="CASCADE"), nullable=False
    )
    admin: Mapped[Admin] = relationship(lazy="subquery")

    tables: Mapped[list["Table"]] = relationship(
        "Table",
        back_populates="location",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return self.name

    @property
    def svg(self):
        return IMAGES_URL + f"{self.id}.svg"


class Table(Base):
    __tablename__ = "tables"

    table_name = mapped_column(String, nullable=False)
    features = mapped_column(JSON, nullable=False, default=[])
    max_people_amount = mapped_column(Integer, default=1, nullable=False)

    location_id = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[Location] = relationship(lazy="subquery")

    def __repr__(self):
        return self.table_name


class Booking(Base):
    __tablename__ = "booking"

    table_id = mapped_column(
        ForeignKey("tables.id", ondelete="CASCADE"), nullable=False
    )
    table: Mapped[Table] = relationship(lazy="subquery")

    time_start = mapped_column(DateTime(timezone=True), nullable=False)
    time_end = mapped_column(DateTime(timezone=True), nullable=False)

    comment = mapped_column(String(520), nullable=True)
    features = mapped_column(JSON, nullable=False, default=[])

    code = mapped_column(String, default=generate_code, nullable=False)
    people_amount = mapped_column(Integer, default=1, nullable=False)

    notification_sent = mapped_column(Boolean, default=False)
    notification_sent_start = mapped_column(Boolean, default=False)
    notification_for_fronted_about_canceled = mapped_column(Boolean, default=False)
    notification_for_fronted_about_start = mapped_column(Boolean, default=False)

    users: Mapped[list["BookingUser"]] = relationship(
        "BookingUser",
        back_populates="booking",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return self.id


class BookingUserStatusEnum(enum.Enum):
    creator = "creator"
    member = "member"


class BookingUser(Base):
    __tablename__ = "booking_user"

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship(lazy="subquery")

    booking_id = mapped_column(
        ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    booking: Mapped[Booking] = relationship(lazy="subquery")

    status = mapped_column(
        Enum(BookingUserStatusEnum),
        nullable=False,
        default=BookingUserStatusEnum.creator,
    )

    notification_sent = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"{self.user_id} - {self.booking_id} - {self.status}"


class QueueUser(Base):
    __tablename__ = "queue_user"

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship(lazy="subquery")

    location_id = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[Location] = relationship(lazy="subquery")

    date = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    hours = mapped_column(Integer, nullable=False)

    comment = mapped_column(String(520), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
