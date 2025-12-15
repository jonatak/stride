import math
from datetime import date, datetime

import polars as pl

from stride.dao import get_pace_series
from stride.types import AppContext, HRInfos, HRZone, PaceStats

ZONE_PCTS: list[tuple[float, float]] = [
    (0.50, 0.60),
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.00),
]

GAP_S = 20 * 60  # 20 minutes


def generate_hr_zone_infos(max_hr: int) -> HRInfos:
    zones: list[HRZone] = []
    prev_max: int | None = None

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


def _format_individual_pace_stats(stat: dict) -> PaceStats:
    period_start = stat["period_start"]
    period_start = f"{period_start}-01"

    s_per_km = int(round(stat["s_per_km"]))
    mn, s = divmod(s_per_km, 60)
    mn_per_km = f"{mn}:{s:02d}"

    return PaceStats(
        period_start=datetime.strptime(period_start, "%Y-%m-%d"),
        mn_per_km=mn_per_km,
        distance_km=int(round(stat["distance_km"])),
    )


def generate_pace_series_monthly(
    ctx: AppContext, start: date, end: date
) -> list[PaceStats]:
    series = get_pace_series(ctx.influx_conn, start, end)
    flatten_serie = [a for i in series for a in i]
    df = pl.DataFrame(flatten_serie)
    df = (
        df.sort(pl.col("time"))
        .with_columns(
            pl.col("time")
            .str.to_datetime("%Y-%m-%dT%H:%M:%SZ")
            .dt.strftime("%Y-%m")
            .alias("period_start"),
            pl.col("distance_m").diff().fill_null(0).alias("dd_m"),
            pl.col("duration_s").diff().fill_null(0).alias("du_s"),
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
        .group_by(
            pl.col("period_start"),
            maintain_order=True,
        )
        .agg(
            (pl.col("dd_m").sum() / 1000).alias("distance_km"),
            (pl.col("du_s").sum() * 1000 / pl.col("dd_m").sum()).alias("s_per_km"),
        )
    )
    result = df.to_dicts()
    return [_format_individual_pace_stats(i) for i in result]
