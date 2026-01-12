from datetime import datetime

from pydantic import BaseModel

from stride.domain.common.schemas import ZonePct


class ActivityInfo(BaseModel):
    activity_id: int
    activity_name: str
    distance_m: float
    duration_s: float
    pace_mn_per_km: str
    avg_hr_bpm: int
    max_hr_bpm: int
    start: datetime
    zones: ZonePct

    @property
    def date_label(self) -> str:
        return self.start.strftime("%d %B, %Y")


class ActivityPoint(BaseModel):
    distance_m: float | None = None
    duration_s: float | None = None
    hr: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    pace_mn_per_km: str | None = None


class ActivitiesResponse(BaseModel):
    series: list[ActivityInfo]


class ActivityInfoResponse(BaseModel):
    activity: ActivityInfo | None = None


class ActivityDetailsResponse(BaseModel):
    series: list[ActivityPoint]
