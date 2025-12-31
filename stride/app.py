from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from stride.api import get_chat_router, get_main_router
from stride.mcp import get_mcp_router
from stride.types import AppContext
from stride.ui import get_ui_router


def create_fast_api_app(ctx: AppContext) -> FastAPI:
    mcp_app = get_mcp_router(ctx)

    app = FastAPI(
        title="Stride",
        description="An api to get relevant garmin data.",
        version="0.1.0",
        lifespan=mcp_app.lifespan,
    )
    app.include_router(get_main_router(ctx), prefix="/api")
    app.include_router(get_chat_router(ctx), prefix="/coach")
    app.include_router(get_ui_router(ctx), prefix="/ui")

    static_dir = Path(__file__).resolve().parent / "ui" / "static"

    app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/mcp", mcp_app)
    return app
