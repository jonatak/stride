import math
from datetime import date

import polars as pl

from stride.domain.dao import get_vo2_max_series, get_weight_series
from stride.domain.types import BodyComposition, HRInfos, HRZone, VO2MaxPoint
from stride.types import AppContext

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


def generate_body_composition_daily_series(
    ctx: AppContext, start: date, end: date
) -> list[BodyComposition]:
    series = get_weight_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    if not flatten_serie:
        return []

    df = pl.DataFrame(flatten_serie)
    df = df.drop_nulls(subset=["weight"]).with_columns(
        pl.col("time")
        .str.to_datetime("%Y-%m-%dT%H:%M:%SZ")
        .dt.strftime("%Y-%m-%d")
        .alias("period_start"),
        pl.col("weight").round(2).alias("weight"),
    )
    result = df.to_dicts()
    return [BodyComposition(**i) for i in result]
