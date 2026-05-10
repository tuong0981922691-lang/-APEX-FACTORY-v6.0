"""Studio Entry — FastAPI application factory (existing pattern).

This is the main entry point for the Apex Factory API.
Runs with: python -m apex_core.orchestrator_v6.studio_entry --serve --port 8787
"""
import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apex_core.auth.router import router as auth_router


def _create_base_app() -> FastAPI:
    app = FastAPI(
        title="APEX Factory",
        version="6.0.0",
        docs_url="/docs",
        redoc_url=None,
    )
    return app


def _setup_authentication(app: FastAPI) -> None:
    """Include auth routers."""
    app.include_router(auth_router)
    # Extension hookup for botthongminh.com v1
    from apex_core.orchestrator_v6._hookup import include_extensions
    include_extensions(app)


def _setup_static_file_serving(app: FastAPI) -> None:
    """Mount public_site/ at /site/."""
    site_dir = Path(__file__).parent.parent.parent / "public_site"
    if site_dir.exists():
        app.mount("/site", StaticFiles(directory=str(site_dir), html=True), name="site")


def _setup_routes(app: FastAPI) -> None:
    """Core system routes."""

    @app.get("/")
    def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/site/portal.html")

    @app.get("/health")
    def health():
        return {"ok": True, "version": "6.0.0", "service": "apex-factory"}


def create_app() -> FastAPI:
    """Application factory."""
    app = _create_base_app()
    _setup_routes(app)
    _setup_authentication(app)
    _setup_static_file_serving(app)
    return app


app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APEX Factory Studio Entry")
    parser.add_argument("--serve", action="store_true", help="Run the server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind")
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        uvicorn.run(
            "apex_core.orchestrator_v6.studio_entry:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
