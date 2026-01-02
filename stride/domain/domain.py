import math
from datetime import date, datetime
from functools import partial
from typing import Literal

import polars as pl

from stride.domain.dao import (
    get_activities_series,
    get_activity_details_series,
    get_activity_info,
    get_pace_series,
    get_vo2_max_series,
)
from stride.types import (
    ActivityInfo,
    ActivityPoint,
    AppContext,
    HRInfos,
    HRZone,
    PaceStats,
    VO2MaxPoint,
    ZonePct,
)

ZONE_PCTS: list[tuple[float, float]] = [
    (0.50, 0.60),
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.00),
]

MAX_HR = 194


def generate_hr_zone_infos() -> HRInfos:
    zones: list[HRZone] = []
    prev_max: int | None = None
    max_hr = MAX_HR
    for i, (pmin, pmax) in enumerate(ZONE_PCTS, start=1):
        min_bpm = math.ceil(pmin * max_hr)
        max_bpm = math.floor(pmax * max_hr)

        if prev_max is not None:
            min_bpm = max(min_bpm, prev_max + 1)

        if i == 5:
            max_bpm = max_hr

        zones.append(HRZone(zone=i, min_bpm=min_bpm, max_bpm=max_bpm))
        prev_max = max_bpm

    return HRInfos(
        max_hr=max_hr,
        zones=zones,
    )


def _calculate_zones(df: pl.DataFrame) -> pl.DataFrame:
    """Calculate and add zone percentages from raw zone seconds."""
    return (
        df.with_columns(
            pl.sum_horizontal("z1_s", "z2_s", "z3_s", "z4_s", "z5_s").alias("total_s")
        )
        .with_columns(
            (pl.col("z1_s") / pl.col("total_s")).alias("z1_pct"),
            (pl.col("z2_s") / pl.col("total_s")).alias("z2_pct"),
            (pl.col("z3_s") / pl.col("total_s")).alias("z3_pct"),
            (pl.col("z4_s") / pl.col("total_s")).alias("z4_pct"),
            (pl.col("z5_s") / pl.col("total_s")).alias("z5_pct"),
        )
        .drop(["z1_s", "z2_s", "z3_s", "z4_s", "z5_s", "total_s"])
    )


def _format_individual_pace_stats(
    stat: dict, dimension: Literal["yearly", "monthly"]
) -> PaceStats:
    match dimension:
        case "monthly":
            period_start = stat["period_start"]
            period_start = f"{period_start}-01"
        case "yearly":
            period_start = stat["period_start"]
            period_start = f"{period_start}-01-01"

    s_per_km = int(round(stat["s_per_km"]))
    mn, s = divmod(s_per_km, 60)
    mn_per_km = f"{mn}:{s:02d}"

    return PaceStats(
        period_start=datetime.strptime(period_start, "%Y-%m-%d"),
        mn_per_km=mn_per_km,
        distance_km=int(round(stat["distance_km"])),
        zones=ZonePct(
            z1=round(stat["z1_pct"], 2),
            z2=round(stat["z2_pct"], 2),
            z3=round(stat["z3_pct"], 2),
            z4=round(stat["z4_pct"], 2),
            z5=round(stat["z5_pct"], 2),
        ),
        count_activities=stat["count_activities"],
    )


def _prepare_columns_for_agg(ctx: AppContext, df: pl.DataFrame) -> pl.DataFrame:
    hr_info = generate_hr_zone_infos()

    hr_expr: None | pl.Expr = None
    for i, zone in enumerate(hr_info.zones, start=1):
        condition = pl.col("hr").is_between(zone.min_bpm, zone.max_bpm)
        if hr_expr is None:
            hr_expr = pl.when(condition).then(pl.lit(i))
        else:
            hr_expr = hr_expr.when(condition).then(pl.lit(i))

    if hr_expr is None:
        raise Exception("unexpected none value for hr_info")

    return (
        df.sort(pl.col("time"))
        .with_columns(
            pl.col("duration_s")
            .diff()
            .over("activity_id")
            .fill_null(pl.col("duration_s"))
            .alias("du_s"),
            pl.col("distance_m")
            .diff()
            .over("activity_id")
            .fill_null(pl.col("distance_m"))
            .alias("dd_m"),
        )
        .with_columns(hr_expr.alias("zone"))
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
    )


def _agg_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by(
            pl.col("period_start"),
            maintain_order=True,
        )
        .agg(
            (pl.col("dd_m").sum() / 1000).alias("distance_km"),
            (pl.col("du_s").sum() * 1000 / pl.col("dd_m").sum()).alias("s_per_km"),
            pl.col("du_s").filter(pl.col("zone") == 1).sum().fill_null(0).alias("z1_s"),
            pl.col("du_s").filter(pl.col("zone") == 2).sum().fill_null(0).alias("z2_s"),
            pl.col("du_s").filter(pl.col("zone") == 3).sum().fill_null(0).alias("z3_s"),
            pl.col("du_s").filter(pl.col("zone") == 4).sum().fill_null(0).alias("z4_s"),
            pl.col("du_s").filter(pl.col("zone") == 5).sum().fill_null(0).alias("z5_s"),
            pl.col("activity_id").n_unique().alias("count_activities"),
        )
        .pipe(_calculate_zones)
    )


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


def generate_pace_series_monthly(
    ctx: AppContext, start: date, end: date
) -> list[PaceStats]:
    series = get_pace_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)

    df = (
        df.pipe(partial(_prepare_columns_for_agg, ctx))
        .with_columns(
            pl.col("time")
            .str.to_datetime("%Y-%m-%dT%H:%M:%SZ")
            .dt.strftime("%Y-%m")
            .alias("period_start")
        )
        .pipe(_agg_dataframe)
    )
    result = df.to_dicts()
    return [_format_individual_pace_stats(i, "monthly") for i in result]


def generate_pace_info_yearly(ctx: AppContext, year: int) -> list[PaceStats]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    series = get_pace_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)

    df = (
        df.pipe(partial(_prepare_columns_for_agg, ctx))
        .with_columns(
            pl.col("time")
            .str.to_datetime("%Y-%m-%dT%H:%M:%SZ")
            .dt.strftime("%Y")
            .alias("period_start")
        )
        .pipe(_agg_dataframe)
    )
    result = df.to_dicts()
    return [_format_individual_pace_stats(i, "yearly") for i in result]


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


def generate_vo2_max_monthly_series(
    ctx: AppContext, start: date, end: date
) -> list[VO2MaxPoint]:
    series = get_vo2_max_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)
    df = df.with_columns(
        pl.col("time")
        .str.to_datetime("%Y-%m-%dT%H:%M:%SZ")
        .dt.strftime("%Y-%m-%d")
        .alias("period_start"),
        pl.col("vo2_max")
        .round(2)
        .fill_null(strategy="forward")
        .fill_null(strategy="backward")
        .alias("vo2_max"),
    )
    result = df.to_dicts()
    return [VO2MaxPoint(**i) for i in result]
