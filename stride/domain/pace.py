from datetime import date, datetime
from functools import partial
from typing import Literal

import polars as pl

from stride.domain.commons import _calculate_zones
from stride.domain.dao import get_pace_series
from stride.domain.types import PaceStats, ZonePct
from stride.types import AppContext

from .health import generate_hr_zone_infos


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
