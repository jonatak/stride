from datetime import date

from fastapi import APIRouter, FastAPI

from stride import domain
from stride.types import AppContext, HRInfos, PaceResponse


def get_router(ctx: AppContext) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.get("/hr/zones")
    def hr_zone() -> HRInfos:
        return domain.generate_hr_zone_infos(ctx.max_hr)

    @router.get("/pace/monthly")
    def pace_monthly(start: date, end: date) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_series_monthly(ctx, start, end))

    return router


def create_fast_api_app(ctx: AppContext) -> FastAPI:
    app = FastAPI(
        title="Stride",
        description="An api to get relevant garmin data.",
        version="0.1.0",
    )
    app.include_router(get_router(ctx))
    return app
