from app.infra.database.models import Booking, Location, Table, User, Admin, BookingUser
from sqladmin import ModelView


class AdminView(ModelView): ...


class AdminAdmin(AdminView, model=Admin):
    column_list = [Admin.login, Admin.id]

    can_edit = False
    can_create = False


class UserAdmin(AdminView, model=User):
    column_list = [User.id, User.username, User.phone]


class LocationAdmin(AdminView, model=Location):
    column_list = [Location.name, Location.address, Location.admin]


class TableAdmin(AdminView, model=Table):
    column_list = [Table.id, Table.location]


class BookingAdmin(AdminView, model=Booking):
    column_list = [Booking.table, Booking.time_start, Booking.time_end, Booking.table_id]


class BookingUserAdmin(AdminView, model=BookingUser):
    column_list = [BookingUser.user, BookingUser.booking, BookingUser.status]
