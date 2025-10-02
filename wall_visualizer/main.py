"""CLI entry point for the wall visualizer."""
from __future__ import annotations

import argparse
from typing import Dict

from .bond import DEFAULT_BOND_NAME, bond_catalog
from .config import DEFAULT_CONFIG, WallConfig
from .controller import WallController
from .renderer import Renderer
from .strategies import BuildStrategy, OptimizedStrideStrategy
from .wall_builder import WallBuilder


def build_strategy_catalog() -> Dict[str, BuildStrategy]:
    optimized = OptimizedStrideStrategy()
    return {optimized.name: optimized}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    bonds = bond_catalog()
    parser = argparse.ArgumentParser(description="Interactive masonry wall build visualizer")
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output",
    )
    parser.add_argument(
        "--scale-mm",
        type=float,
        default=10.0,
        help="Wall width represented per character (default: 10mm)",
    )
    parser.add_argument(
        "--bond",
        choices=sorted(bonds.keys()),
        default=DEFAULT_BOND_NAME,
        help="Select the brick bond pattern",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config: WallConfig = DEFAULT_CONFIG
    bond = bond_catalog()[args.bond]
    builder = WallBuilder(config=config, bond=bond)
    wall = builder.build()

    strategies = build_strategy_catalog()
    initial_strategy = next(iter(strategies.keys()))
    renderer = Renderer(config=config, use_colour=not args.no_colour, scale_mm=args.scale_mm)
    controller = WallController(
        wall=wall,
        strategies=strategies,
        renderer=renderer,
        initial_strategy=initial_strategy,
    )
    controller.run()


if __name__ == "__main__":
    main()
