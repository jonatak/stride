import math

from stride.types import HRInfos, HRZone

ZONE_PCTS: list[tuple[float, float]] = [
    (0.50, 0.60),
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.00),
]


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
