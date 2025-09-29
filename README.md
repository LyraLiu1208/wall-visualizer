# Wall Visualizer

Interactive CLI program that models a 2300 mm × 2000 mm stretcher bond wall, renders the plan as ASCII art, and lets you step through brick placement一块砖一块砖地铺设。当前版本仅保留优化后的铺设顺序：按照机器人 stride（800 mm × 1300 mm 工作包络）分区，最大化每次停留时可放置的砖块。

The code is intentionally modular so it is easy to add new bonds or optimisation strategies later.

## Requirements

- Python 3.10+
- Terminal that supports ANSI colours (optional – use `--no-colour` otherwise).

## Usage

```bash
python -m wall_visualizer [options]
```

Useful flags:

- `--no-colour` – disable ANSI colours; stride IDs fall back to distinct characters.
- `--scale-mm <value>` – horizontal millimetres represented by one character (default: 10).

### Controls

- `<Enter>` – lay the next brick in the current strategy (the upcoming brick is shown with a lighter shade).
- `r` – reset progress for the current strategy.
- `h` – print a short help message.
- `q` – quit.

The legend at the bottom shows stride IDs, mapped 3×2 for the default wall size。

## Project Structure

```
wall_visualizer/
  bond.py            # Bond generators (currently stretcher bond)
  config.py          # Dimensional constants and helpers
  controller.py      # Interactive loop & command handling
  models.py          # Dataclasses for bricks, strides, wall
  renderer.py        # ASCII/ANSI renderer
  strategies.py      # Stride-optimized build order (extensible)
  wall_builder.py    # Geometry construction & stride assignment
  main.py            # CLI wiring
```

## Extending

- Add new bond patterns by implementing `BondStrategy.generate_course` and wiring it into `WallBuilder`.
- Create additional build strategies by subclassing `BuildStrategy` and registering it in `build_strategy_catalog`.

Tests are not included yet; run the CLI interactively to verify behaviour.
