from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .system import router as system_router





no_system_router = APIRouter(prefix="/api/v1")
no_system_router.include_router(auth_router)
no_system_router.include_router(users_router)

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(no_system_router)