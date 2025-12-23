from dataclasses import dataclass
from datetime import date, datetime

from influxdb import InfluxDBClient
from pydantic import BaseModel, Field


class HRZone(BaseModel):
    zone: int = Field(ge=1, le=5)
    min_bpm: int
    max_bpm: int


class HRInfos(BaseModel):
    max_hr: int
    zones: list[HRZone]


@dataclass
class AppContext:
    max_hr: int
    influx_conn: InfluxDBClient


class ZonePct(BaseModel):
    z1: float
    z2: float
    z3: float
    z4: float
    z5: float


class PaceStats(BaseModel):
    period_start: date
    mn_per_km: str
    distance_km: int
    count_activities: int
    zones: ZonePct


class PaceResponse(BaseModel):
    series: list[PaceStats]


class ActivityInfo(BaseModel):
    activity_id: str
    activity_name: str
    distance_m: float
    duration_s: float
    pace_mn_per_km: str
    avg_hr_bpm: int
    max_hr_bpm: int
    start: datetime

    zones: ZonePct


class ActivitiesResponse(BaseModel):
    series: list[ActivityInfo]
