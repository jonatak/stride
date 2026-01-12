from datetime import date

from pydantic import BaseModel

from stride.domain.common.schemas import ZonePct


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
