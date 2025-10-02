# Wall Visualizer

Interactive CLI for planning masonry walls within an 800 mm × 1300 mm robotic stride envelope. The simulator renders a 2300 mm × 2000 mm wall as ASCII art, highlights stride regions, and lets you step through a robot-friendly build order one brick at a time.

## Highlights
- Multiple brick bonds out of the box: `stretcher`, `flemish`, `english-cross`, and constraint-aware `wild` bond.
- Optimised placement order that batches bricks by stride to minimise slow drive/lift motions.
- Rich terminal visual: colour-coded strides (or fallback symbols when `--no-colour` is used).
- Modular architecture: bonds, build strategies, and rendering logic live in separate modules for easy extension.

## Requirements
- Python 3.10+
- A terminal with ANSI colour support is recommended (colours can be disabled via `--no-colour`).

## Usage
```bash
python -m wall_visualizer [options]
```

### Common options
- `--bond {stretcher,flemish,english-cross,wild}` – switch between available brick bonds (default: `stretcher`).
- `--scale-mm <value>` – number of millimetres represented by a single character (default: `10`).
- `--no-colour` – render using ASCII symbols instead of ANSI colours.

> **Wild bond note:** the generator uses pseudorandom search bounded by masonry rules (no stacked head joints, limited “falling teeth”, no interior half-brick pairs). Adjust the seed in `WildBond(seed=...)` if you want deterministic output.

### Controls (during the session)
- `<Enter>` – place the next brick.
- `r` – reset progress for the current strategy.
- `h` – show inline help.
- `q` – quit.
- `m` – (only when multiple build strategies are registered) cycle to the next strategy.

Built bricks appear as solid blocks, the next scheduled brick uses a lighter shade, and unbuilt bricks remain stippled. A legend at the bottom maps stride IDs to their positions in the wall grid.

## Project Layout
```
wall_visualizer/
  bond.py            # BondStrategy implementations (stretcher, flemish, english-cross, wild)
  config.py          # Wall and brick dimensions plus utility accessors
  controller.py      # Interactive REPL loop and command handling
  models.py          # Dataclasses for bricks, specs, strides, and walls
  renderer.py        # ASCII/ANSI renderer for the wall state
  strategies.py      # BuildStrategy implementations (optimised stride sequence)
  wall_builder.py    # Geometry construction and stride assignment
  main.py            # CLI entry point
```

## Extending
- **New bonds:** subclass `BondStrategy`, implement `generate_course`, and register the strategy in `bond_catalog()` so the CLI can expose it.
- **New build orders:** subclass `BuildStrategy`, implement `order_bricks`, then add it to `build_strategy_catalog()` in `main.py`.
- **Renderer tweaks:** customise glyphs or colours by editing `renderer.py`.

Run `python -m compileall wall_visualizer` to perform a quick syntax check after making changes.
