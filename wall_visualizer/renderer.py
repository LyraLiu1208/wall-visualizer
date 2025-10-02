"""ASCII renderer for the wall state."""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .config import WallConfig
from .models import Brick, Wall

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

STRIDE_SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # degrade without colour
STRIDE_COLOURS = ["\033[38;5;33m", "\033[38;5;208m", "\033[38;5;142m", "\033[38;5;197m", "\033[38;5;111m", "\033[38;5;220m", "\033[38;5;99m", "\033[38;5;214m"]


class Renderer:
    def __init__(self, config: WallConfig, use_colour: bool = True, scale_mm: float = 10.0) -> None:
        self.config = config
        self.use_colour = use_colour
        self.scale_mm = scale_mm
        self.line_width = int(round(config.wall_width_mm / scale_mm))
        if self.line_width <= 0:
            raise ValueError("Scale produces zero-width render line")

    def render(
        self,
        wall: Wall,
        built_bricks: Iterable[int],
        strategy_name: str,
        strategy_description: str,
        summary: str,
        next_brick_id: int | None,
        commands_hint: str,
    ) -> str:
        built_set = set(built_bricks)
        lines: List[str] = []

        lines.append(f"Strategy: {strategy_name} – {strategy_description}")
        if summary:
            lines.append(summary)
        lines.append(f"Commands: {commands_hint}")

        for course in reversed(range(self.config.course_count())):
            course_bricks = [b for b in wall.bricks if b.course_index == course]
            course_line = self._render_course(course_bricks, built_set, next_brick_id)
            lines.append(course_line)
        lines.append(self._render_stride_legend(wall))
        return "\n".join(lines)

    def _render_course(
        self,
        bricks: Sequence[Brick],
        built_set: set[int],
        next_brick_id: int | None,
    ) -> str:
        chars: List[str] = [" "] * self.line_width
        for brick in bricks:
            start = int(round(brick.x_mm / self.scale_mm))
            end = int(round((brick.x_mm + brick.length_mm) / self.scale_mm))
            start = max(start, 0)
            end = min(end, self.line_width)
            if start >= end:
                continue
            char = "░"
            if brick.brick_id in built_set:
                char = "█"
            elif next_brick_id is not None and brick.brick_id == next_brick_id:
                char = "▒"
            glyph = self._colourise(char, brick.stride_id, brick.brick_id in built_set)
            for idx in range(start, end):
                chars[idx] = glyph
        return "".join(chars)

    def _colourise(self, symbol: str, stride_id: int | None, built: bool) -> str:
        if stride_id is None:
            return symbol
        if not self.use_colour:
            base = STRIDE_SYMBOLS[stride_id % len(STRIDE_SYMBOLS)]
            if symbol == "█":
                return base.upper()
            if symbol == "░":
                return base.lower()
            if symbol == "▒":
                return base
            return symbol
        colour = STRIDE_COLOURS[stride_id % len(STRIDE_COLOURS)]
        if built:
            return f"{ANSI_BOLD}{colour}{symbol}{ANSI_RESET}"
        return f"{colour}{symbol}{ANSI_RESET}"

    def _render_stride_legend(self, wall: Wall) -> str:
        seen: Dict[int, str] = {}
        entries: List[str] = []
        for stride in sorted(wall.strides, key=lambda s: s.stride_id):
            token = self._colourise("█", stride.stride_id, True)
            if token in seen.values():
                token = self._colourise("█", stride.stride_id + 1, True)
            label = f"stride {stride.stride_id} (col={stride.col}, row={stride.row})"
            entries.append(f"{token} {label}")
            seen[stride.stride_id] = token
        return "Legend: " + ", ".join(entries)
