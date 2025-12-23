from datetime import date
from typing import Annotated

from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from stride import domain
from stride.types import ActivitiesResponse, AppContext, HRInfos, PaceResponse


def get_router(ctx: AppContext) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/hr/zones")
    def hr_zone() -> HRInfos:
        return domain.generate_hr_zone_infos(ctx.max_hr)

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

    return router


def get_ui_router(ctx: AppContext) -> APIRouter:
    router = APIRouter(prefix="/ui")
    templates = Jinja2Templates(directory="templates")

    @router.get("/pace/monthly", response_class=HTMLResponse)
    def pace_monthly_ui(
        request: Request,
        start: date | None = None,
        end: date | None = None,
    ):
        if start is None or end is None:
            year = date.today().year
            start = date(year, 1, 1)
            end = date(year, 12, 31)

        return templates.TemplateResponse(
            "progress.html",
            {
                "request": request,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "active_page": "progress",
            },
        )

    @router.get("/home", response_class=HTMLResponse)
    def home_ui(request: Request):
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "active_page": "home",
            },
        )

    return router


def create_fast_api_app(ctx: AppContext) -> FastAPI:
    app = FastAPI(
        title="Stride",
        description="An api to get relevant garmin data.",
        version="0.1.0",
    )
    app.include_router(get_router(ctx))
    app.include_router(get_ui_router(ctx))
    return app
