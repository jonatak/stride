from dataclasses import dataclass

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
