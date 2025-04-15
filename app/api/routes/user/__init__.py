from app.api.routes.user.auth import router as auth_router
from app.api.routes.user.book import router as book_router
from app.api.routes.user.groups import router as groups_router
from app.api.routes.user.queue import router as queue_router
from fastapi import APIRouter

router = APIRouter(prefix="/users")

router.include_router(auth_router)
router.include_router(book_router)
router.include_router(groups_router)
router.include_router(queue_router)
