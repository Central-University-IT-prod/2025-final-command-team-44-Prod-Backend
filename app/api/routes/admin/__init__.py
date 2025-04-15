from app.api.routes.admin.auth import router as auth_router
from app.api.routes.admin.location import router as location_router
from app.api.routes.admin.tables import router as tables_router
from fastapi import APIRouter

router = APIRouter(prefix="/admins")

router.include_router(auth_router)
router.include_router(location_router)
router.include_router(tables_router)
