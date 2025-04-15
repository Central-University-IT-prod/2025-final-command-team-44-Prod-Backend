from app.infra.database.models import Location
from app.infra.repository.admin import AdminRepository
from app.infra.repository.user import UserRepository
from app.services.location import LocationService

USERS = [
    dict(username="ZaharDimidov", id=749234118, first_name="Zahar"),
    dict(username="dzzzzz77", id=7485502073, first_name="Dim"),
]

ADMINS = [dict(id="admin_1_id", login="my_admin", password=f"abcd123")]

LOCATIONS = [
    dict(id=f"location_2_id", name="Огниково", address=f"Москва"),
    dict(id=f"location_3_id", name="Яндекс", address=f"Москва"),
    dict(id=f"location_4_id", name="TSpace", address=f"Грузинский вал 7"),
]

TABLES = [dict(id=f"table_{i}_id", table_name=f"table_{i}_name") for i in range(1, 3)]


async def init():
    for user in USERS:
        await UserRepository().get_or_create(**user)

    for admin in ADMINS:
        last_admin = await AdminRepository().get_or_create(**admin)

    for location in LOCATIONS:
        last_location: Location = await LocationService().repo.get_or_create(
            **location, admin_id=last_admin.id
        )

    for table in TABLES:
        await LocationService().tables.get_or_create(
            **table, location_id=last_location.id
        )

    with open("src/test-view.svg", "rb") as file:
        location = await LocationService().set_svg(last_location.id, file.read())
   