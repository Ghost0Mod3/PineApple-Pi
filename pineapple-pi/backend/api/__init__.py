from fastapi import APIRouter
from .system import router as system_router
from .radios import router as radios_router
from .networks import router as networks_router
from .scanner import router as scanner_router
from .settings import router as settings_router
api_router=APIRouter()
for router in (system_router,radios_router,networks_router,scanner_router,settings_router): api_router.include_router(router)
