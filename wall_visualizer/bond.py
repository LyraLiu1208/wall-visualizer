"""Bond strategies define horizontal brick layouts per course."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from .config import WallConfig
from .models import BrickKind, BrickSpec


class BondError(ValueError):
    """Raised when a strategy cannot satisfy the requested configuration."""


class BondStrategy:
    """Interface for bond-specific course generation."""

    name: str = "base"

    def reset(self, config: WallConfig) -> None:  # pragma: no cover - default hook
        del config

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        raise NotImplementedError

    # Shared helpers -----------------------------------------------------

    @staticmethod
    def _sequence_width(sequence: Sequence[BrickSpec], config: WallConfig) -> float:
        total = 0.0
        for idx, brick in enumerate(sequence):
            total += brick.length_mm
            if idx < len(sequence) - 1:
                total += config.head_joint_mm
        return total

    @staticmethod
    def _brick(kind: BrickKind, config: WallConfig, metadata: dict | None = None) -> BrickSpec:
        return BrickSpec(kind=kind, length_mm=config.length_for_kind(kind.value), metadata=metadata)

    def _validate_wall_width(self, sequence: Sequence[BrickSpec], config: WallConfig) -> None:
        width = self._sequence_width(sequence, config)
        if abs(width - config.wall_width_mm) > 1e-6:
            raise BondError(
                f"Generated course width {width} does not match wall width {config.wall_width_mm}"
            )


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

        self._validate_wall_width(sequence, config)
        return sequence

    def _generate_even_course(self, total_units: int, config: WallConfig) -> List[BrickSpec]:
        half_count = 1
        while (total_units - half_count) % 2 != 0:
            half_count += 2
        full_count = (total_units - half_count) // 2
        if full_count < 2:
            raise BondError("Even course cannot be constructed with fewer than two full bricks")

        full_left = full_count // 2
        full_right = full_count - full_left

        sequence: List[BrickSpec] = []
        sequence.extend(self._repeat(BrickKind.FULL, full_left, config))
        sequence.extend(self._repeat(BrickKind.HALF, 1, config))
        sequence.extend(self._repeat(BrickKind.FULL, full_right, config))
        return sequence

    def _generate_odd_course(self, total_units: int, config: WallConfig) -> List[BrickSpec]:
        half_count = 2
        while (total_units - half_count) % 2 != 0:
            half_count += 1
        full_count = (total_units - half_count) // 2
        if full_count < 1:
            raise BondError("Odd course requires at least one full brick")

        full_left = full_count // 2
        full_right = full_count - full_left
        interior_half = half_count - 2

        sequence: List[BrickSpec] = []
        sequence.extend(self._repeat(BrickKind.HALF, 1, config))
        sequence.extend(self._repeat(BrickKind.FULL, full_left, config))
        while interior_half > 0:
            sequence.extend(self._repeat(BrickKind.HALF, 1, config))
            interior_half -= 1
            if full_right > 0:
                sequence.extend(self._repeat(BrickKind.FULL, 1, config))
                full_right -= 1
        sequence.extend(self._repeat(BrickKind.FULL, full_right, config))
        sequence.extend(self._repeat(BrickKind.HALF, 1, config))
        return sequence

    def _repeat(self, kind: BrickKind, count: int, config: WallConfig) -> List[BrickSpec]:
        if count <= 0:
            return []
        return [self._brick(kind, config) for _ in range(count)]


@dataclass
class FlemishBond(BondStrategy):
    """Alternating headers and stretchers with staggered starters each course."""

    name: str = "flemish"

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        start_kind = BrickKind.HEADER if course_index % 2 == 0 else BrickKind.FULL
        alt_kind = BrickKind.FULL if start_kind == BrickKind.HEADER else BrickKind.HEADER

        sequence: List[BrickSpec] = []
        current_width = 0.0
        expected = start_kind
        while True:
            brick = self._brick(expected, config)
            if sequence:
                current_width += config.head_joint_mm
            current_width += brick.length_mm
            if current_width - config.wall_width_mm > 1e-6:
                raise BondError("Flemish bond could not align with wall width")
            sequence.append(brick)
            if abs(current_width - config.wall_width_mm) <= 1e-6:
                break
            expected = alt_kind if expected == start_kind else start_kind
        self._validate_wall_width(sequence, config)
        return sequence


@dataclass
class EnglishCrossBond(BondStrategy):
    """Alternate courses of stretchers and headers with central cross headers."""

    name: str = "english-cross"

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        if course_index % 2 == 0:
            sequence = self._stretcher_course(config)
        else:
            sequence = self._header_course(config)
        self._validate_wall_width(sequence, config)
        return sequence

    def _header_course(self, config: WallConfig) -> List[BrickSpec]:
        header_count = config.total_half_modules()
        return [self._brick(BrickKind.HEADER, config) for _ in range(header_count)]

    def _stretcher_course(self, config: WallConfig) -> List[BrickSpec]:
        modules = config.total_half_modules()
        if modules < 3:
            raise BondError("English cross bond requires at least three half modules")

        remaining = modules - 2  # reserve for edge halves
        header_modules = 1
        if (remaining - header_modules) % 2 != 0:
            raise BondError("Wall width incompatible with English cross stretcher course")

        full_count = (remaining - header_modules) // 2
        full_left = math.ceil(full_count / 2)
        full_right = full_count - full_left

        sequence: List[BrickSpec] = [self._brick(BrickKind.HALF, config)]
        sequence.extend(self._repeat(BrickKind.FULL, full_left, config))
        sequence.append(self._brick(BrickKind.HEADER, config, metadata={"role": "cross"}))
        sequence.extend(self._repeat(BrickKind.FULL, full_right, config))
        sequence.append(self._brick(BrickKind.HALF, config))
        return sequence

    def _repeat(self, kind: BrickKind, count: int, config: WallConfig) -> List[BrickSpec]:
        if count <= 0:
            return []
        return [self._brick(kind, config) for _ in range(count)]


@dataclass
class WildBond(BondStrategy):
    """Pseudo-random wild bond respecting artisanal constraints."""

    name: str = "wild"
    seed: int | None = None
    max_attempts: int = 500
    max_overlap_ratio: float = 0.35
    _rng: random.Random = field(init=False, repr=False)
    _previous_joints: List[List[float]] = field(default_factory=list, init=False, repr=False)
    _step_direction: int = field(default=0, init=False, repr=False)
    _step_run: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def reset(self, config: WallConfig) -> None:
        del config
        self._previous_joints.clear()
        self._step_direction = 0
        self._step_run = 0

    def generate_course(self, course_index: int, config: WallConfig) -> List[BrickSpec]:
        for _ in range(self.max_attempts):
            sequence = self._attempt_sequence(config)
            joints = self._joint_positions(sequence, config)
            if self._violates_prev_course(joints, config):
                continue
            direction = self._step_direction_for(joints)
            if direction == 0:
                self._step_run = 0
            elif direction == self._step_direction:
                if self._step_run >= 6:
                    continue
                self._step_run += 1
            else:
                self._step_direction = direction
                self._step_run = 1
            self._previous_joints.append(joints)
            if len(self._previous_joints) > 2:
                self._previous_joints.pop(0)
            self._validate_wall_width(sequence, config)
            return sequence
        raise BondError("Unable to generate wild bond course within attempt budget")

    def _attempt_sequence(self, config: WallConfig) -> List[BrickSpec]:
        modules = config.total_half_modules()
        half_module = config.half_module_mm
        prev_sets = [
            {int(round(pos / half_module)) for pos in joints}
            for joints in self._previous_joints
        ]
        overlap_limit = self._overlap_limit(config)

        increments: List[int] = []
        overlap_counts = [0 for _ in prev_sets]
        solution: List[int] | None = None

        def backtrack(used_modules: int, half_count: int, full_count: int) -> bool:
            nonlocal solution
            if used_modules == modules:
                if half_count == 0 or full_count == 0:
                    return False
                solution = increments.copy()
                return True

            options = [1, 2]
            self._rng.shuffle(options)
            for step in options:
                if used_modules + step > modules:
                    continue
                if step == 1 and increments:
                    last_step = increments[-1]
                    is_edge = used_modules == 0 or used_modules + step == modules
                    if last_step == 1 and not is_edge:
                        continue

                new_overlaps = overlap_counts.copy()
                next_modules = used_modules + step
                if next_modules < modules:
                    module_index = next_modules
                    violate = False
                    for idx, prev in enumerate(prev_sets):
                        if module_index in prev:
                            new_overlaps[idx] += 1
                            if new_overlaps[idx] > overlap_limit:
                                violate = True
                                break
                    if violate:
                        continue

                increments.append(step)
                prev_counts = overlap_counts.copy()
                overlap_counts[:] = new_overlaps
                if backtrack(
                    next_modules,
                    half_count + (1 if step == 1 else 0),
                    full_count + (1 if step == 2 else 0),
                ):
                    return True
                overlap_counts[:] = prev_counts
                increments.pop()
            return False

        if not backtrack(0, 0, 0):
            raise BondError("Unable to satisfy wild bond course width")

        sequence: List[BrickSpec] = []
        for step in solution or []:
            kind = BrickKind.HALF if step == 1 else BrickKind.FULL
            sequence.append(self._brick(kind, config))
        return sequence

    def _joint_positions(self, sequence: Sequence[BrickSpec], config: WallConfig) -> List[float]:
        pos = 0.0
        joints: List[float] = []
        for idx, spec in enumerate(sequence):
            pos += spec.length_mm
            if idx < len(sequence) - 1:
                pos += config.head_joint_mm
                joints.append(pos)
        return joints

    def _violates_prev_course(self, joints: List[float], config: WallConfig) -> bool:
        if not self._previous_joints:
            return False
        tolerance = config.head_joint_mm / 2.0
        overlap_limit = self._overlap_limit(config)
        for prev in self._previous_joints:
            overlaps = 0
            for joint in joints:
                if any(abs(joint - prev_joint) <= tolerance for prev_joint in prev):
                    overlaps += 1
                    if overlaps > overlap_limit:
                        return True
        return False

    def _overlap_limit(self, config: WallConfig) -> int:
        modules = config.total_half_modules() - 1
        return max(1, int(math.floor(modules * self.max_overlap_ratio)))

    def _step_direction_for(self, joints: List[float]) -> int:
        if len(self._previous_joints) < 1:
            return 0
        prev = self._previous_joints[-1]
        limit = min(len(prev), len(joints))
        signs = set()
        for idx in range(limit):
            delta = joints[idx] - prev[idx]
            if abs(delta) <= 1e-3:
                continue
            signs.add(1 if delta > 0 else -1)
        if len(signs) == 1:
            return signs.pop()
        return 0


def bond_catalog() -> dict[str, BondStrategy]:
    return {
        StretcherBond().name: StretcherBond(),
        FlemishBond().name: FlemishBond(),
        EnglishCrossBond().name: EnglishCrossBond(),
        WildBond().name: WildBond(),
    }


DEFAULT_BOND_NAME = StretcherBond().name


def default_bond() -> BondStrategy:
    return StretcherBond()
