from fastapi import APIRouter, Query
from backend.services.inventory import list_access_points, inventory_summary
router=APIRouter(prefix="/networks",tags=["Networks"])
@router.get("")
def networks(limit:int=Query(200,ge=1,le=1000)): return {"items":list_access_points(limit)}
@router.get("/summary")
def summary(): return inventory_summary()
