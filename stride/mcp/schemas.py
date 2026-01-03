from pydantic import BaseModel

from stride.domain.types import (
    ActivityInfo,
    ActivityPoint,
    HRInfos,
    PaceStats,
    VO2MaxPoint,
)


class PaceResponse(BaseModel):
    series: list[PaceStats]


class ActivitiesResponse(BaseModel):
    series: list[ActivityInfo]


class ActivityInfoResponse(BaseModel):
    activity: ActivityInfo | None = None


class ActivityDetailsResponse(BaseModel):
    series: list[ActivityPoint]


class VO2MaxResponse(BaseModel):
    series: list[VO2MaxPoint]


class HRInfosResponse(BaseModel):
    info: HRInfos


class McpActivityResponse(BaseModel):
    info: ActivityInfo
    details: list[ActivityPoint]
