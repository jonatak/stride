from datetime import date

from fastapi import APIRouter

from stride.domain.activities.schemas import (
    ActivitiesResponse,
    ActivityDetailsResponse,
    ActivityInfoResponse,
)
from stride.domain.activities.service import (
    generate_activities_infos,
    generate_activity_details_serie,
    generate_activity_info_by_id,
)
from stride.types import AppContext


def get_activities_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.get("/activities")
    def activities(start: date, end: date) -> ActivitiesResponse:
        return ActivitiesResponse(series=generate_activities_infos(ctx, start, end))

    @router.get("/activities/details/{activity_id}")
    def activity_details(activity_id: int) -> ActivityDetailsResponse:
        return ActivityDetailsResponse(
            series=generate_activity_details_serie(ctx, activity_id)
        )

    @router.get("/activities/{activity_id}")
    def activity_info(activity_id: int) -> ActivityInfoResponse:
        return ActivityInfoResponse(activity=generate_activity_info_by_id(ctx, activity_id))

    return router
