from fastapi import APIRouter, FastAPI

from stride import domain
from stride.types import AppContext, HRInfos, HRZone


def get_router(ctx: AppContext) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.get("/hr/zones")
    def hr_zone():
        return domain.generate_hr_zone_infos(ctx.max_hr)

    return router


def create_fast_api_app(ctx: AppContext) -> FastAPI:
    app = FastAPI(
        title="Stride",
        description="An api to get relevant garmin data.",
        version="0.1.0",
    )
    app.include_router(get_router(ctx))
    return app
