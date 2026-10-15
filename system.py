from fastapi import APIRouter
from backend.services.system_monitor import get_system_health
router=APIRouter(prefix="/system",tags=["System"])
@router.get("/health")
def health(): return get_system_health()
