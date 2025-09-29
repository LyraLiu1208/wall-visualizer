"""Interactive controller for stepping through build sequences."""
from __future__ import annotations

from typing import Dict, List

from .models import Wall
from .renderer import Renderer
from .strategies import BuildStrategy


class WallController:
    def __init__(
        self,
        wall: Wall,
        strategies: Dict[str, BuildStrategy],
        renderer: Renderer,
        initial_strategy: str,
    ) -> None:
        if initial_strategy not in strategies:
            raise ValueError(f"Unknown strategy '{initial_strategy}'")
        self.wall = wall
        self.strategies = strategies
        self.renderer = renderer
        self.strategy_names: List[str] = list(strategies.keys())
        self.current_strategy_name = initial_strategy
        self._multiple_strategies = len(self.strategy_names) > 1
        self.orders: Dict[str, List[int]] = {
            name: strategy.order_bricks(wall) for name, strategy in strategies.items()
        }
        self.status_message = ""
        self._reset_progress()

    def run(self) -> None:
        while True:
            self._render()
            try:
                command = input("Action> ").strip().lower()
            except EOFError:
                print()
                return
            if command == "":
                if not self._advance():
                    self.status_message = "Wall complete. Reset or switch strategy to continue."
                continue
            if command == "q":
                return
            if command == "r":
                self._reset_progress()
                self.status_message = "Progress reset."
                continue
            if command == "m":
                if self._multiple_strategies:
                    self._cycle_strategy()
                else:
                    self.status_message = "Only the optimized strategy is available."
                continue
            if command == "h":
                self._show_help()
                continue
            self.status_message = "Unknown command. Press 'h' for help."

    # Internal helpers -------------------------------------------------

    def _render(self) -> None:
        order = self.orders[self.current_strategy_name]
        next_brick_id = order[self.progress] if self.progress < len(order) else None
        built_so_far = order[: self.progress]
        strategy = self.strategies[self.current_strategy_name]
        summary = strategy.summarize(self.wall, order)
        screen = self.renderer.render(
            wall=self.wall,
            built_bricks=built_so_far,
            strategy_name=strategy.name,
            strategy_description=strategy.description,
            summary=summary,
            next_brick_id=next_brick_id,
            commands_hint=self._commands_hint(),
        )
        print("\033[H\033[J", end="")  # clear screen
        print(screen)
        if self.status_message:
            print()
            print(self.status_message)

    def _advance(self) -> bool:
        order = self.orders[self.current_strategy_name]
        if self.progress >= len(order):
            return False
        brick_id = order[self.progress]
        self.progress += 1
        brick = self.wall.brick_by_id(brick_id)
        self.status_message = (
            f"Placed brick {brick.brick_id} (course={brick.course_index}, stride={brick.stride_id}, "
            f"kind={brick.kind.value})."
        )
        return True

    def _reset_progress(self) -> None:
        self.progress = 0

    def _cycle_strategy(self) -> None:
        idx = self.strategy_names.index(self.current_strategy_name)
        next_idx = (idx + 1) % len(self.strategy_names)
        self.current_strategy_name = self.strategy_names[next_idx]
        self._reset_progress()
        self.status_message = f"Switched to strategy '{self.current_strategy_name}'. Progress reset."

    def _show_help(self) -> None:
        self.status_message = "Commands: " + self._commands_hint()

    def _commands_hint(self) -> str:
        commands = ["<Enter>=next", "r=reset", "h=help", "q=quit"]
        if self._multiple_strategies:
            commands.insert(1, "m=next strategy")
        return ", ".join(commands)
