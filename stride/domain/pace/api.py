from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path

from stride.domain.pace.schemas import PaceResponse
from stride.domain.pace.service import generate_pace_info_yearly, generate_pace_series_monthly
from stride.types import AppContext


def get_pace_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.get("/pace/monthly")
    def pace_monthly(start: date, end: date) -> PaceResponse:
        return PaceResponse(series=generate_pace_series_monthly(ctx, start, end))

    @router.get("/summary/yearly/{year}")
    def pace_yearly(
        year: Annotated[int, Path(title="The year of the summary", ge=2021, lt=2050)],
    ) -> PaceResponse:
        return PaceResponse(series=generate_pace_info_yearly(ctx, year))

    return router
