# gcode-swap: speed (M220 + F scale), print temps, inspect

**Date**: 2026-04-07  
**Status**: completed

## Goal
Add optional M220 feedrate percent, optional F-word scaling in the executable block, absolute bed/tool temp overrides only during the print phase (after first `;LAYER_CHANGE` through `; filament end gcode`), and `--inspect` to summarize layers/speeds/temps/colors.

## Steps
1. Regex/helpers: executable bounds, print temp window, F scaling, M command + G9111 patching
2. Wire into `process_gcode` after swap output; extend CLI
3. Implement `run_inspect`; README touch-up

## Key decisions
- Print phase for temps: first `;LAYER_CHANGE` through line before `; filament end gcode` (else `EXECUTABLE_BLOCK_END`). Skip rewriting when target S is 0 (cooldown).
- F scaling: only between `EXECUTABLE_BLOCK_START` and `EXECUTABLE_BLOCK_END` when present; else whole file for non-comment G0–G3 lines.
- M220 inserted after first `; AFTER_LAYER_CHANGE` following first `;LAYER_CHANGE`.
- Tool temp map: `--tool-temps 220,225` → T0,T1; or `0:220,1:225`.

## Files affected
- `tools/gcode-swap.py`
- `README.md`

## Outcome
Implemented in `tools/gcode-swap.py`: `apply_speed_and_temperature_post` runs after swap output (not on `--dry-run`). Verified on `tools/lineswap.gcode`: `M140 S60`→`S55`, `F18000`→`F10800` at 60%, `M220 S60` after first layer, `M220 S100` before end gcode. `--inspect` reports layers, F stats, temps, `extruder_colour` / `paint_info`.
