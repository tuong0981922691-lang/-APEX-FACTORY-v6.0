"""Main botthongminh.com router — aggregates all sub-routers."""
from fastapi import APIRouter

from apex_core.orchestrator_v6.c2_hub_router import router as c2_hub_router
from apex_core.orchestrator_v6.orders_router import router as orders_router
from apex_core.orchestrator_v6.recovery_router import router as recovery_router
from apex_core.orchestrator_v6.twofa_router import router as twofa_router

router = APIRouter()

router.include_router(c2_hub_router)
router.include_router(orders_router)
router.include_router(twofa_router)
router.include_router(recovery_router)


@router.get("/health")
def botthongminh_health():
    """Health check for botthongminh.com extension."""
    return {
        "status": "ok",
        "service": "botthongminh",
        "modules": ["c2_hub", "orders", "twofa", "recovery"],
        "kill_switch": False,
    }
