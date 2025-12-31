from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from fastmcp import FastMCP
from fastmcp.server.http import StarletteWithLifespan

from stride import domain
from stride.types import (
    ActivitiesResponse,
    ActivityDetailsResponse,
    AppContext,
    HRInfos,
    PaceResponse,
)


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
    def get_hr_zones() -> HRInfos:
        return domain.generate_hr_zone_infos()

    @mcp.tool()
    def get_last_activities(days: int) -> ActivitiesResponse:
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=days)).replace(day=1)

        return ActivitiesResponse(
            series=domain.generate_activities_infos(ctx, start, end)
        )

    @mcp.tool()
    def get_activity_details(activity_id: int) -> ActivityDetailsResponse:
        return ActivityDetailsResponse(
            series=domain.generate_activity_details_serie(ctx, activity_id)
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

    return mcp.http_app(path="/", transport="streamable-http")
