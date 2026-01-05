from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from fastmcp import FastMCP
from fastmcp.server.http import StarletteWithLifespan

from stride import domain
from stride.mcp.schemas import (
    ActivitiesResponse,
    ActivityResponse,
    BodyCompositionResponse,
    HRInfosResponse,
    PaceResponse,
    VO2MaxResponse,
)
from stride.types import AppContext


def get_mcp_router(ctx: AppContext) -> StarletteWithLifespan:
    mcp = FastMCP("Stride MCP Server")

    @mcp.tool()
    def get_yearly_summary(year: int) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_info_yearly(ctx, year))

    @mcp.tool()
    def get_monthly_summaries(start: date, end: date) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_series_monthly(ctx, start, end))

    @mcp.tool()
    def get_last_n_monthly_summaries(months: int) -> PaceResponse:
        end = date.today() + timedelta(days=1)
        start = date.today() - relativedelta(months=months)
        return PaceResponse(series=domain.generate_pace_series_monthly(ctx, start, end))

    @mcp.tool()
    def get_hr_zones() -> HRInfosResponse:
        return HRInfosResponse(info=domain.generate_hr_zone_infos())

    @mcp.tool()
    def get_last_activities(days: int) -> ActivitiesResponse:
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=days)).replace(day=1)

        return ActivitiesResponse(
            series=domain.generate_activities_infos(ctx, start, end)
        )

    @mcp.tool()
    def get_activity_details_by_id(activity_id: int) -> ActivityResponse | None:
        info = domain.generate_activity_info_by_id(ctx, activity_id)
        if not info:
            return None
        return ActivityResponse(
            info=info,
            details=domain.generate_activity_details_serie(ctx, activity_id),
        )

    @mcp.tool()
    def get_activity_details_by_date(
        year: int, month: int, day: int
    ) -> ActivityResponse | None:
        start = date(year, month, day)
        end = date(year, month, day + 1)
        data = domain.generate_activities_infos(ctx, start, end)
        if len(data) == 0:
            return None
        return ActivityResponse(
            info=data[0],
            details=domain.generate_activity_details_serie(ctx, data[0].activity_id),
        )

    @mcp.tool
    def get_current_datetime():
        """Return the current datetime (Europe/Paris) and UTC."""
        now_utc = datetime.now(timezone.utc)
        now_paris = now_utc.astimezone(ZoneInfo("Europe/Paris"))
        return {
            "utc": now_utc.isoformat(),
            "paris": now_paris.isoformat(),
            "date_paris": now_paris.date().isoformat(),
        }

    @mcp.tool()
    def get_vo2max_trend(past_days: int) -> VO2MaxResponse:
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=past_days)).replace(day=1)

        return VO2MaxResponse(
            series=domain.generate_vo2_max_daily_series(ctx, start, end)
        )

    @mcp.tool()
    def get_body_composition_trend(past_days: int) -> BodyCompositionResponse:
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=past_days)).replace(day=1)

        return BodyCompositionResponse(
            series=domain.generate_body_composition_daily_series(ctx, start, end)
        )

    return mcp.http_app(path="/", transport="streamable-http")
