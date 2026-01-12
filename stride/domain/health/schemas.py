from datetime import date

from pydantic import BaseModel, Field, computed_field

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

    @computed_field
    @property
    def label(self) -> str:
        return ZONE_LABELS[self.zone]


class HRInfos(BaseModel):
    max_hr: int
    zones: list[HRZone]


class VO2MaxPoint(BaseModel):
    period_start: date
    vo2_max: float


class BodyComposition(BaseModel):
    period_start: date
    weight: float


class HRInfosResponse(BaseModel):
    info: HRInfos


class VO2MaxResponse(BaseModel):
    series: list[VO2MaxPoint]


class BodyCompositionResponse(BaseModel):
    series: list[BodyComposition]
