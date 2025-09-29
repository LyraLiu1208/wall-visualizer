"""Bond strategies define horizontal brick layouts per course."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .config import WallConfig
from .models import BrickKind, BrickSpec


class BondStrategy:
    """Interface for bond-specific course generation."""

    name: str = "base"

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        raise NotImplementedError


@dataclass
class StretcherBond(BondStrategy):
    """Classic stretcher bond with alternating half-brick offsets."""

    name: str = "stretcher"

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        total_units = config.total_half_modules()
        is_even = course_index % 2 == 0

        if is_even:
            sequence = self._generate_even_course(total_units, config)
        else:
            sequence = self._generate_odd_course(total_units, config)

        # Validate the resulting width matches expectations.
        width = self._sequence_width(sequence, config)
        if abs(width - config.wall_width_mm) > 1e-6:
            raise ValueError(
                f"Generated course width {width} does not match wall width {config.wall_width_mm}"
            )
        return sequence

    @staticmethod
    def _sequence_width(sequence: Iterable[BrickSpec], config: WallConfig) -> float:
        total = 0.0
        seq = list(sequence)
        for idx, brick in enumerate(seq):
            total += brick.width_mm
            if idx < len(seq) - 1:
                total += config.head_joint_mm
        return total

    def _generate_even_course(self, total_units: int, config: WallConfig) -> List[BrickSpec]:
        # Even courses start and end with full bricks.
        half_count = 1
        while (total_units - half_count) % 2 != 0:
            half_count += 2
        full_count = (total_units - half_count) // 2
        if full_count < 2:
            raise ValueError("Even course cannot be constructed with fewer than two full bricks")

        full_left = full_count // 2
        full_right = full_count - full_left

        sequence: List[BrickSpec] = []
        sequence.extend(self._brick_repeat(BrickKind.FULL, full_left, config))
        sequence.extend(self._brick_repeat(BrickKind.HALF, 1, config))
        sequence.extend(self._brick_repeat(BrickKind.FULL, full_right, config))
        return sequence

    def _generate_odd_course(self, total_units: int, config: WallConfig) -> List[BrickSpec]:
        # Odd courses start and end with half bricks.
        half_count = 2
        while (total_units - half_count) % 2 != 0:
            half_count += 1
        full_count = (total_units - half_count) // 2
        if full_count < 1:
            raise ValueError("Odd course requires at least one full brick")

        full_left = full_count // 2
        full_right = full_count - full_left
        interior_half = half_count - 2

        sequence: List[BrickSpec] = []
        sequence.extend(self._brick_repeat(BrickKind.HALF, 1, config))
        sequence.extend(self._brick_repeat(BrickKind.FULL, full_left, config))
        while interior_half > 0:
            sequence.extend(self._brick_repeat(BrickKind.HALF, 1, config))
            interior_half -= 1
            if full_right > 0:
                sequence.extend(self._brick_repeat(BrickKind.FULL, 1, config))
                full_right -= 1
        sequence.extend(self._brick_repeat(BrickKind.FULL, full_right, config))
        sequence.extend(self._brick_repeat(BrickKind.HALF, 1, config))
        return sequence

    def _brick_repeat(self, kind: BrickKind, count: int, config: WallConfig) -> List[BrickSpec]:
        if count <= 0:
            return []
        width = (
            config.brick_full.length if kind == BrickKind.FULL else config.brick_half_length_mm
        )
        return [BrickSpec(kind=kind, width_mm=width) for _ in range(count)]


DEFAULT_BOND = StretcherBond()
