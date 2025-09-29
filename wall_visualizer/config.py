"""Configuration and constants for the wall visualizer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrickSize:
    length: float
    width: float
    height: float


@dataclass(frozen=True)
class WallConfig:
    wall_width_mm: float = 2300.0
    wall_height_mm: float = 2000.0
    brick_full: BrickSize = BrickSize(length=210.0, width=100.0, height=50.0)
    brick_half_length_mm: float = 100.0
    head_joint_mm: float = 10.0
    bed_joint_mm: float = 12.5
    course_height_mm: float = 62.5
    stride_width_mm: float = 800.0
    stride_height_mm: float = 1300.0

    def course_count(self) -> int:
        return int(round(self.wall_height_mm / self.course_height_mm))

    @property
    def half_module_mm(self) -> float:
        """Nominal length of a half-brick plus head joint."""
        return self.brick_half_length_mm + self.head_joint_mm

    @property
    def full_module_mm(self) -> float:
        return self.brick_full.length + self.head_joint_mm

    def total_half_modules(self) -> int:
        """Total number of half-brick modules that fit along the wall width.

        We add one head joint to account for the final joint that is excluded when
        summing bricks. This ensures the module count remains an integer for valid
        configurations.
        """
        total = self.wall_width_mm + self.head_joint_mm
        module = self.half_module_mm
        if abs(round(total / module) - total / module) > 1e-6:
            raise ValueError(
                "Wall width does not align to half-brick modules with current configuration"
            )
        return int(round(total / module))


DEFAULT_CONFIG = WallConfig()
