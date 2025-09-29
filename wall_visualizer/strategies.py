"""Build strategies determine the order bricks are placed."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .models import Brick, Wall


class BuildStrategy:
    name: str = "base"
    description: str = ""

    def order_bricks(self, wall: Wall) -> List[int]:
        raise NotImplementedError

    def summarize(self, wall: Wall, order: Iterable[int]) -> str:
        del wall, order
        return ""
@dataclass
class OptimizedStrideStrategy(BuildStrategy):
    """Groups bricks by stride to minimize slow robot motions."""

    name: str = "optimized"
    description: str = (
        "Bottom stride row first, left-to-right across strides, then move platform up;"
        " serpentine traversal inside each stride."
    )

    def order_bricks(self, wall: Wall) -> List[int]:
        stride_order = sorted(
            wall.strides,
            key=lambda s: (s.row, s.col),
        )

        ordered: List[int] = []
        for stride in stride_order:
            bricks = [wall.brick_by_id(bid) for bid in stride.bricks]
            bricks.sort(key=lambda b: (b.course_index, b.x_mm))
            current_course = None
            course_bricks: List[Brick] = []

            def flush_course(course_list: List[Brick]) -> None:
                if not course_list:
                    return
                course_idx = course_list[0].course_index
                reverse = course_idx % 2 == 1
                course_list.sort(key=lambda b: b.x_mm, reverse=reverse)
                ordered.extend(b.brick_id for b in course_list)

            for brick in bricks:
                if current_course is None:
                    current_course = brick.course_index
                    course_bricks = [brick]
                    continue
                if brick.course_index != current_course:
                    flush_course(course_bricks)
                    current_course = brick.course_index
                    course_bricks = [brick]
                else:
                    course_bricks.append(brick)
            flush_course(course_bricks)
        return ordered

    def summarize(self, wall: Wall, order: Iterable[int]) -> str:
        order_list = order if isinstance(order, list) else list(order)
        stride_sequence = [wall.brick_by_id(bid).stride_id for bid in order_list]
        switches = 0
        last_stride = None
        for stride_id in stride_sequence:
            if last_stride is None:
                last_stride = stride_id
                continue
            if stride_id != last_stride:
                switches += 1
                last_stride = stride_id
        distinct = len({s for s in stride_sequence})
        return (
            f"stride switches={switches}, distinct strides={distinct}, total bricks={len(order_list)}"
        )


DEFAULT_OPTIMIZED = OptimizedStrideStrategy()
DEFAULT_STRATEGIES = {
    DEFAULT_OPTIMIZED.name: DEFAULT_OPTIMIZED,
}
