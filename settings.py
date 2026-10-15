from fastapi import APIRouter
from backend.config import settings
router=APIRouter(prefix="/settings",tags=["Settings"])
@router.get("")
def public_settings(): return {"management_interface":settings.management_interface,"scanner_interface":settings.scanner_interface,"scan_interval_seconds":settings.scan_interval_seconds,"active_radio_changes_enabled":settings.allow_active_radio_changes}
