from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path

from stride import domain
from stride.types import (
    ActivitiesResponse,
    ActivityDetailsResponse,
    ActivityInfoResponse,
    AppContext,
    HRInfos,
    PaceResponse,
)


def get_main_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.get("/hr/zones")
    def hr_zone() -> HRInfos:
        return domain.generate_hr_zone_infos()

    @router.get("/pace/monthly")
    def pace_monthly(start: date, end: date) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_series_monthly(ctx, start, end))

    @router.get("/summary/yearly/{year}")
    def pace_yearly(
        year: Annotated[int, Path(title="The year of the summary", ge=2021, lt=2050)],
    ) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_info_yearly(ctx, year))

    @router.get("/activities")
    def activities(start: date, end: date) -> ActivitiesResponse:
        return ActivitiesResponse(
            series=domain.generate_activities_infos(ctx, start, end)
        )

    @router.get("/activities/details/{activity_id}")
    def activity_details(activity_id: int) -> ActivityDetailsResponse:
        return ActivityDetailsResponse(
            series=domain.generate_activity_details_serie(ctx, activity_id)
        )

    @router.get("/activities/{activity_id}")
    def activity_info(activity_id: int) -> ActivityInfoResponse:
        return ActivityInfoResponse(
            activity=domain.generate_activity_info_by_id(ctx, activity_id)
        )

    return router
