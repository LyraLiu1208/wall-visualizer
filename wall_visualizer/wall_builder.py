"""Constructs the wall geometry from a given configuration and bond."""
from __future__ import annotations

import math
from typing import List

from .bond import BondStrategy, DEFAULT_BOND
from .config import DEFAULT_CONFIG, WallConfig
from .models import Brick, BrickKind, Stride, Wall


class WallBuilder:
    def __init__(self, config: WallConfig | None = None, bond: BondStrategy | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self.bond = bond or DEFAULT_BOND

    def build(self) -> Wall:
        bricks = self._generate_bricks()
        strides = self._generate_strides()
        self._assign_strides(bricks, strides)
        return Wall(config=self.config, bricks=bricks, strides=strides)

    def _generate_bricks(self) -> List[Brick]:
        bricks: List[Brick] = []
        course_count = self.config.course_count()
        head_joint = self.config.head_joint_mm
        course_height = self.config.course_height_mm
        brick_height = self.config.brick_full.height

        brick_id = 0
        for course_idx in range(course_count):
            y = course_idx * course_height
            sequence = self.bond.generate_course(course_idx, self.config)
            x = 0.0
            for index_in_course, spec in enumerate(sequence):
                bricks.append(
                    Brick(
                        brick_id=brick_id,
                        course_index=course_idx,
                        index_in_course=index_in_course,
                        kind=spec.kind,
                        x_mm=x,
                        y_mm=y,
                        width_mm=spec.width_mm,
                        height_mm=brick_height,
                    )
                )
                brick_id += 1
                x += spec.width_mm
                if index_in_course < len(sequence) - 1:
                    x += head_joint
        return bricks

    def _generate_strides(self) -> List[Stride]:
        stride_width = self.config.stride_width_mm
        stride_height = self.config.stride_height_mm
        wall_width = self.config.wall_width_mm
        wall_height = self.config.wall_height_mm

        cols = max(1, math.ceil(wall_width / stride_width))
        rows = max(1, math.ceil(wall_height / stride_height))

        strides: List[Stride] = []
        stride_id = 0
        for row in range(rows):
            y = row * stride_height
            height = min(stride_height, wall_height - y)
            for col in range(cols):
                x = col * stride_width
                width = min(stride_width, wall_width - x)
                strides.append(
                    Stride(
                        stride_id=stride_id,
                        row=row,
                        col=col,
                        x_mm=x,
                        y_mm=y,
                        width_mm=width,
                        height_mm=height,
                    )
                )
                stride_id += 1
        return strides

    def _assign_strides(self, bricks: List[Brick], strides: List[Stride]) -> None:
        stride_width = self.config.stride_width_mm
        stride_height = self.config.stride_height_mm
        cols = max(1, math.ceil(self.config.wall_width_mm / stride_width))
        rows = max(1, math.ceil(self.config.wall_height_mm / stride_height))

        for brick in bricks:
            col = min(int(brick.center_x // stride_width), cols - 1)
            row = min(int(brick.center_y // stride_height), rows - 1)
            stride_index = row * cols + col
            brick.stride_id = stride_index
            strides[stride_index].bricks.append(brick.brick_id)
