from fastapi import APIRouter
from backend.services.radio_manager import get_radio_statuses
router=APIRouter(prefix="/radios",tags=["Radios"])
@router.get("")
def radios(): return {"items":get_radio_statuses()}
