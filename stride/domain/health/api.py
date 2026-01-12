from datetime import date

from fastapi import APIRouter

from stride.domain.health.schemas import (
    BodyCompositionResponse,
    HRInfosResponse,
    VO2MaxResponse,
)
from stride.domain.health.service import (
    generate_body_composition_daily_series,
    generate_hr_zone_infos,
    generate_vo2_max_daily_series,
)
from stride.types import AppContext


def get_health_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.get("/hr/zones")
    def hr_zone() -> HRInfosResponse:
        return HRInfosResponse(info=generate_hr_zone_infos())

    @router.get("/vo2max")
    def vo2max(start: date, end: date) -> VO2MaxResponse:
        return VO2MaxResponse(series=generate_vo2_max_daily_series(ctx, start, end))

    @router.get("/bodycomposition/daily")
    def body_composition(start: date, end: date) -> BodyCompositionResponse:
        return BodyCompositionResponse(
            series=generate_body_composition_daily_series(ctx, start, end)
        )

    return router
