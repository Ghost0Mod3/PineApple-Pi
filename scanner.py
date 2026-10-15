from fastapi import APIRouter, HTTPException
from backend.services.scanner import scan_and_store
router=APIRouter(prefix="/scanner",tags=["Scanner"])
@router.post("/run")
def run_scan():
    try: return scan_and_store()
    except RuntimeError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc
