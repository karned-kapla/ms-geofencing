from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Zone(BaseModel):
    polygon: list[list[int]] = Field(min_length=3)
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    min_object_size: int = Field(gt=0)

    @field_validator("polygon")
    @classmethod
    def polygon_points_must_be_pairs(cls, v: list[list[int]]) -> list[list[int]]:
        for point in v:
            if len(point) != 2:
                raise ValueError(f"Each polygon point must have exactly 2 coordinates, got {point}")
        return v


class IntrusionEvent(BaseModel):
    timestamp: datetime
    bbox: tuple[int, int, int, int]          # x, y, w, h
    video_source: str
    frame_width: int
    frame_height: int
    polygon: list[list[int]]
    capture_path: Optional[str] = None
    service_id: Optional[str] = None

