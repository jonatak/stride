from datetime import date

import polars as pl

from stride.domain.activities.dao import (
    get_activities_series,
    get_activity_details_series,
    get_activity_info,
)
from stride.domain.activities.schemas import ActivityInfo, ActivityPoint
from stride.domain.common.schemas import ZonePct
from stride.domain.common.zone_utils import _calculate_zones
from stride.types import AppContext


def _process_activity_data(df: pl.DataFrame) -> pl.DataFrame:
    """Common processing for activity data: calculate zones."""
    return df.with_columns(
        pl.col("time").str.to_datetime(strict=False, time_zone="UTC").alias("ts"),
        (1000 / pl.col("avg_speed_m_per_s")).alias("pace_s_per_km"),
    ).pipe(_calculate_zones)


def _format_individual_activity_info(info: dict) -> ActivityInfo:
    s_per_km = int(round(info["pace_s_per_km"]))
    mn, s = divmod(s_per_km, 60)
    mn_per_km = f"{mn}:{s:02d}"

    return ActivityInfo(
        activity_id=info["activity_id"],
        activity_name=info["activity_name"],
        start=info["time"],
        pace_mn_per_km=mn_per_km,
        distance_m=int(round(info["distance_m"])),
        duration_s=int(round(info["duration_s"])),
        avg_hr_bpm=info["avg_hr_bpm"],
        max_hr_bpm=info["max_hr_bpm"],
        zones=ZonePct(
            z1=round(info["z1_pct"], 2),
            z2=round(info["z2_pct"], 2),
            z3=round(info["z3_pct"], 2),
            z4=round(info["z4_pct"], 2),
            z5=round(info["z5_pct"], 2),
        ),
    )


def generate_activities_infos(
    ctx: AppContext, start: date, end: date
) -> list[ActivityInfo]:
    series = get_activities_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)
    df = (
        _process_activity_data(df)
        .sort(["activity_id", "ts"])
        .unique(subset=["activity_id"], keep="last")
        .sort(["ts"], descending=True)
        .drop("ts")
    )
    result = df.to_dicts()
    return [_format_individual_activity_info(i) for i in result]


def generate_activity_info_by_id(
    ctx: AppContext, activity_id: int
) -> ActivityInfo | None:
    """Fetch activity info by activity_id."""
    # First try the direct query (may return empty depending on Influx schema)
    series = get_activity_info(ctx.influx_conn, activity_id)
    flatten_serie = [a for i in series for a in i]

    if not flatten_serie:
        return None

    df = pl.DataFrame(flatten_serie)
    df = _process_activity_data(df).drop("ts")

    result = df.to_dicts()
    if not result:
        return None

    return _format_individual_activity_info(result[0])


def generate_activity_details_serie(
    ctx: AppContext, activity_id: int
) -> list[ActivityPoint]:
    """Fetch detailed activity points for a specific activity."""
    series = get_activity_details_series(ctx.influx_conn, activity_id)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)
    df = (
        df.with_columns(
            pl.col("duration_s").diff().alias("du_s"),
            pl.col("distance_m").diff().alias("dd_m"),
        )
        .with_columns(
            pl.when(pl.col("dd_m") >= 0)
            .then(pl.col("dd_m"))
            .otherwise(0)
            .alias("dd_m"),
            pl.when(pl.col("du_s") >= 0)
            .then(pl.col("du_s"))
            .otherwise(0)
            .alias("du_s"),
        )
        .with_columns(
            pl.when(pl.col("dd_m") > 0)
            .then(pl.col("du_s") * 1000 / pl.col("dd_m"))
            .otherwise(None)
            .alias("s_per_km")
        )
        .with_columns(pl.col("hr").round().alias("hr"))
        .filter(pl.col("s_per_km") < 600)
        .drop("dd_m", "du_s")
    )

    def _format_point(d: dict):
        if d.get("s_per_km"):
            s_per_km = int(round(d["s_per_km"]))
            mn, s = divmod(s_per_km, 60)
            mn_per_km = f"{mn}:{s:02d}"
            d["pace_mn_per_km"] = mn_per_km
        return ActivityPoint(**d)

    return [_format_point(i) for i in df.to_dicts()]
