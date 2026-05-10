"""Extension loader for botthongminh.com v1 routers."""
from fastapi import FastAPI


def include_extensions(app: FastAPI) -> None:
    """Include all botthongminh.com extension routers."""
    from apex_core.orchestrator_v6.c2_hub_router import router as c2_router
    from apex_core.orchestrator_v6.orders_router import router as orders_router
    from apex_core.orchestrator_v6.recovery_router import router as recovery_router
    from apex_core.orchestrator_v6.twofa_router import router as twofa_router
    from apex_core.routers.botthongminh_router import router as btm_router

    app.include_router(c2_router)
    app.include_router(orders_router)
    app.include_router(twofa_router)
    app.include_router(recovery_router)
    app.include_router(btm_router, prefix="/api/v1", tags=["botthongminh"])
