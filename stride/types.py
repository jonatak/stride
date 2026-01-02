from dataclasses import dataclass
from datetime import date, datetime

from influxdb import InfluxDBClient
from pydantic import BaseModel, Field, computed_field
from pydantic_ai import Agent


class ChatRequest(BaseModel):
    message: str


class ChatStreamResponse(BaseModel):
    delta: str = ""
    done: bool = False
    error: str = ""


ZONE_LABELS: dict[int, str] = {
    1: "Very Easy (Warm-up / Recovery)",
    2: "Easy",
    3: "Aerobic",
    4: "Threshold",
    5: "VO₂ Max",
}


class HRZone(BaseModel):
    zone: int = Field(ge=1, le=5)
    min_bpm: int
    max_bpm: int

    @computed_field  # included in model_dump/model_dump_json
    @property
    def label(self) -> str:
        return ZONE_LABELS[self.zone]


class HRInfos(BaseModel):
    max_hr: int
    zones: list[HRZone]


@dataclass
class AppContext:
    influx_conn: InfluxDBClient
    agent: Agent | None = None


@dataclass
class AgentContext:
    mcp_url: str
    agent_model: str
    agent_base_url: str
    agent_api_key: str


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

    @property
    def date_label(self) -> str:
        return self.period_start.strftime("%d %B, %Y")


class PaceResponse(BaseModel):
    series: list[PaceStats]


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


class ActivitiesResponse(BaseModel):
    series: list[ActivityInfo]


class ActivityInfoResponse(BaseModel):
    activity: ActivityInfo | None = None


class ActivityPoint(BaseModel):
    distance_m: float | None = None
    duration_s: float | None = None
    hr: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    pace_mn_per_km: str | None = None


class ActivityDetailsResponse(BaseModel):
    series: list[ActivityPoint]


class VO2MaxPoint(BaseModel):
    period_start: date
    vo2_max: float


class VO2MaxResponse(BaseModel):
    series: list[VO2MaxPoint]
