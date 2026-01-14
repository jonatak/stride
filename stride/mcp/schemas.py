from pydantic import BaseModel

from stride.domain.activities.schemas import ActivityInfo, ActivityPoint
from stride.domain.health.schemas import BodyComposition, HRInfos, VO2MaxPoint
from stride.domain.pace.schemas import PaceStats


class PaceResponse(BaseModel):
    series: list[PaceStats]


class WorkoutsResponse(BaseModel):
    series: list[ActivityInfo]


class ActivityInfoResponse(BaseModel):
    activity: ActivityInfo | None = None


class ActivityDetailsResponse(BaseModel):
    series: list[ActivityPoint]


class VO2MaxResponse(BaseModel):
    series: list[VO2MaxPoint]


class HRInfosResponse(BaseModel):
    info: HRInfos


class WorkoutDetailsResponse(BaseModel):
    info: ActivityInfo
    details: list[ActivityPoint]


class BodyCompositionResponse(BaseModel):
    series: list[BodyComposition]
