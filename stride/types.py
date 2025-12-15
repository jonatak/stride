from dataclasses import dataclass
from datetime import date

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


class PaceStats(BaseModel):
    period_start: date
    mn_per_km: str
    distance_km: int
    # z2_avg_mn_per_km: float
    # z2_median_mn_per_km: float


class PaceResponse(BaseModel):
    series: list[PaceStats]
