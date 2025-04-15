from fastapi import APIRouter
from fastapi.routing import APIRoute

from app.api.routes.admin import router as admin_router
from app.api.routes.location import router as location_router
from app.api.routes.user import router as user_router

router = APIRouter(prefix="/api")


@router.get("/ping", status_code=200, summary="Пинг", tags=["Пинг"])
def ping():
    return {"status": "ok"}


for r in [user_router, admin_router, location_router]:
    router.include_router(r)

for route in router.routes:
    if isinstance(route, APIRoute):
        route.response_model_exclude_none = True
        parts = route.name.split("_")
        route.operation_id = "".join(map(str.capitalize, parts))
