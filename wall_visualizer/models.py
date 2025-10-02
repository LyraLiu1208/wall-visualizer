"""Data models for walls, bricks, and strides."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Sequence

from .config import WallConfig


class BrickKind(str, Enum):
    FULL = "full"
    HALF = "half"
    HEADER = "header"
    THREE_QUARTER = "three_quarter"
    QUARTER = "quarter"


@dataclass(frozen=True)
class BrickSpec:
    kind: BrickKind
    length_mm: float
    metadata: dict | None = None


@dataclass
class Brick:
    brick_id: int
    course_index: int
    index_in_course: int
    kind: BrickKind
    x_mm: float
    y_mm: float
    length_mm: float
    height_mm: float
    stride_id: int | None = None

    @property
    def center_x(self) -> float:
        return self.x_mm + self.length_mm / 2

    @property
    def center_y(self) -> float:
        return self.y_mm + self.height_mm / 2


@dataclass
class Stride:
    stride_id: int
    row: int
    col: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    bricks: List[int] = field(default_factory=list)


@dataclass
class Wall:
    config: WallConfig
    bricks: List[Brick]
    strides: List[Stride]

    def brick_by_id(self, brick_id: int) -> Brick:
        return self.bricks[brick_id]

    def bricks_in_course(self, course_index: int) -> Sequence[Brick]:
        return [b for b in self.bricks if b.course_index == course_index]
