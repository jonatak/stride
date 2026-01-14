from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from fastmcp import FastMCP
from fastmcp.prompts import Message
from fastmcp.server.http import StarletteWithLifespan
from loguru import logger

from stride.domain.activities.service import (
    generate_activities_infos,
    generate_activity_details_serie,
    generate_activity_info_by_id,
)
from stride.domain.health.service import (
    generate_body_composition_daily_series,
    generate_hr_zone_infos,
    generate_vo2_max_daily_series,
)
from stride.domain.pace.service import (
    generate_pace_series_monthly,
    generate_pace_series_weekly,
)
from stride.mcp.schemas import (
    BodyCompositionResponse,
    HRInfosResponse,
    PaceResponse,
    VO2MaxResponse,
    WorkoutDetailsResponse,
    WorkoutsResponse,
)
from stride.types import AppContext


def get_mcp_router(ctx: AppContext) -> StarletteWithLifespan:
    mcp = FastMCP("Stride MCP Server")

    @mcp.tool()
    def get_workouts_monthly_summary(months: int) -> PaceResponse:
        """Return workouts summaries over the last N months.

        Use when:
        - You need recent training context (volume, intensity distribution, distance, and zones)

        Args:
            months: Lookback window in months, relative to current datetime.

        Returns:
            PaceResponse containing a time series of the past few months summary.
        """
        logger.info("tool_call get_workouts_monthly_summary months={}", months)
        end = date.today() + timedelta(days=1)
        start = date.today() - relativedelta(months=months)
        return PaceResponse(series=generate_pace_series_monthly(ctx, start, end))

    @mcp.tool()
    def get_workouts_weekly_summary(weeks: int) -> PaceResponse:
        """Return workouts summaries over the last N weeks.

        Semantics:
            - Weeks start on Monday (ISO week, Europe/Paris).
            - The most recent week MAY be PARTIAL (current week in progress).
            - Earlier weeks are full weeks.


        Use when:
        - You need recent training context (volume, intensity distribution, distance, and zones)

        Args:
            weeks: Lookback window in weeks, relative to current datetime.

        Returns:
            PaceResponse containing a time series of the past few weeks summary.
        """
        logger.info("tool_call get_workouts_weekly_summary weeks={}", weeks)
        end = date.today()
        end = end - timedelta(days=end.weekday()) + relativedelta(weeks=1)
        start = date.today() - relativedelta(weeks=weeks)
        return PaceResponse(series=generate_pace_series_weekly(ctx, start, end))

    @mcp.tool()
    def get_hr_zones() -> HRInfosResponse:
        """Return user HR zones."""
        logger.info("tool_call get_hr_zones")
        return HRInfosResponse(info=generate_hr_zone_infos())

    @mcp.tool()
    def get_last_workouts(days: int) -> WorkoutsResponse:
        """Return all running activities in the last N days.

        Use when:
        - You need recent training context (volume, intensity distribution).
        - You want to identify recent key sessions.

        Do not use when:
        - You only need aggregated trends (prefer get_last_n_monthly_summaries).

        Args:
        days: Lookback window in days, relative to the current datetime (Europe/Paris).
                Includes activities whose start_time is >= now - days.

        Returns:
        ActivitiesResponse containing a list of activities with ids, dates, distance, duration,
        pace stats, HR stats, and zone distribution (if available).

        Example:
        - Last week overview: get_last_activities(days=7)
        - Last month context: get_last_activities(days=30)
        """
        logger.info("tool_call get_last_workouts days={}", days)
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=days)).replace(day=1)

        return WorkoutsResponse(series=generate_activities_infos(ctx, start, end))

    @mcp.tool()
    def get_workout_details_by_id(activity_id: int) -> WorkoutDetailsResponse | None:
        """Return the workout details for a certain activity_id.

        Use when:
        - you need detail information for some activities (hr, duration, distance, altitude and pace for each time interval.)

        Returns:
            WorkoutDetailsResponse containing a summary of the activities as well as the detailed timeserie.
        """
        logger.info("tool_call get_workout_details_by_id activity_id={}", activity_id)
        info = generate_activity_info_by_id(ctx, activity_id)
        if not info:
            return None
        return WorkoutDetailsResponse(
            info=info,
            details=generate_activity_details_serie(ctx, activity_id),
        )

    @mcp.tool()
    def get_workout_details_by_date(
        year: int, month: int, day: int
    ) -> WorkoutDetailsResponse | None:
        """Return the workout details for a certain date.

        Use when:
        - you need detail information for some activities (hr, duration, distance, altitude and pace for each time interval.)

        Returns:
            WorkoutDetailsResponse containing a summary of the activities as well as the detailed timeserie.
        """
        logger.info(
            "tool_call get_workout_details_by_date year={} month={} day={}",
            year,
            month,
            day,
        )
        start = date(year, month, day)
        end = date(year, month, day + 1)
        data = generate_activities_infos(ctx, start, end)
        if len(data) == 0:
            return None
        return WorkoutDetailsResponse(
            info=data[0],
            details=generate_activity_details_serie(ctx, data[0].activity_id),
        )

    @mcp.tool()
    def get_current_datetime():
        """Return the current datetime (Europe/Paris) and UTC."""
        logger.info("tool_call get_current_datetime")
        now_utc = datetime.now(timezone.utc)
        now_paris = now_utc.astimezone(ZoneInfo("Europe/Paris"))
        return {
            "utc": now_utc.isoformat(),
            "paris": now_paris.isoformat(),
            "date_paris": now_paris.date().isoformat(),
        }

    @mcp.tool()
    def get_vo2max_trend(past_days: int) -> VO2MaxResponse:
        """Return the vo2max trend over the last N days.

        Args:
            past_days: Lookback window in days, relative to the current datetime (Europe/Paris).
                    Includes activities whose start_time is >= now - days.
        """
        logger.info("tool_call get_vo2max_trend past_days={}", past_days)
        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=past_days)).replace(day=1)

        return VO2MaxResponse(series=generate_vo2_max_daily_series(ctx, start, end))

    @mcp.tool()
    def get_body_composition_trend(past_days: int) -> BodyCompositionResponse:
        """Return the body composition trend over the last N days.

        Use when:
            - you want the weight trend of the user.

        Args:
            past_days: Lookback window in days, relative to the current datetime (Europe/Paris).
                    Includes activities whose start_time is >= now - days.
        """
        logger.info("tool_call get_body_composition_trend past_days={}", past_days)

        end = date.today() + timedelta(days=1)
        start = (date.today() - timedelta(days=past_days)).replace(day=1)

        return BodyCompositionResponse(
            series=generate_body_composition_daily_series(ctx, start, end)
        )

    return mcp.http_app(path="/", transport="streamable-http")
