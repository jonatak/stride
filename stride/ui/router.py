from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from stride.types import AppContext


def get_ui_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()
    templates_dir = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    def default_dates():
        end = date.today() + timedelta(days=1)
        start = end - timedelta(days=7)
        return start, end

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
            "monthly_summary.html",
            {
                "request": request,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "active_page": "monthly_summary",
            },
        )

    @router.get("/home", response_class=HTMLResponse)
    def home_ui(request: Request):
        start, end = default_dates()
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "active_page": "home",
            },
        )

    @router.get("/activities", response_class=HTMLResponse)
    def activities_ui(
        request: Request,
        start: date | None = None,
        end: date | None = None,
    ):
        if start is None or end is None:
            start, end = default_dates()

        return templates.TemplateResponse(
            "activities.html",
            {
                "request": request,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "active_page": "activities",
            },
        )

    @router.get("/activities/details/{activity_id}", response_class=HTMLResponse)
    def activity_details_ui(
        request: Request,
        activity_id: int,
    ):
        return templates.TemplateResponse(
            "activity_details.html",
            {
                "request": request,
                "activity_id": activity_id,
                "active_page": "activities",
            },
        )

    return router
