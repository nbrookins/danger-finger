# Parametric Pass 2: Automated Improvements

**Date**: 2026-04-11  
**Status**: in-progress

## Goal
Second pass of automated parametric model improvements, focusing on changes that are safe to make without visual review: expanded validation, broader test coverage, safe magic number derivation, and documenting what still needs human visual inspection.

## Steps
1. Expand `validate_params()` with more cross-parameter constraints (tunnel vs intermediate, linkage geometry, bumper vs knuckle, tip interface proportions)
2. Extend sweep tests to cover ALL parts, not just middle
3. Add profile-level validation tests and multi-param interaction tests
4. Derive magic numbers where the formula is unambiguous from physical relationships
5. Document remaining magic numbers that require visual review (with candidate formulas)
6. Run full test suite and verify all changes pass
7. Update QA stabilization plan with outcomes

## Key decisions
- Only derive constants where the physical relationship is obvious and verifiable at default params; flag the rest for visual review
- Extend sweep to all parts but keep STUPIDFAST quality for speed
- Add interaction tests for known-dangerous param pairs (from cascade table in parametric-consistency rule)
- Do NOT change any geometry code that would require visual verification

## Files affected
- `danger/finger_params.py` — expanded `validate_params()`
- `danger/finger.py` — safe constant derivations + documentation
- `tests/test_param_sweep.py` — all-parts sweep, interaction tests
- `tests/test_profiles.py` — profile validation
- `docs/CODEBASE_NOTES.md` — magic number audit

## Outcome
**Status**: completed

- 261 tests pass (up from ~95 in pass 1), all in 112s on Python 3.9
- `validate_params()` expanded with 10 new cross-parameter constraints (tunnel, linkage, bumper, socket interface, bottom strut, tip print)
- Sweep tests now cover all 8 geometry parts at param boundaries (was only middle)
- 10 known-dangerous param interaction pairs tested at all 4 corners (min/min, min/max, max/min, max/max)
- 7 profiles validated: validate_params, all-parts SCAD, preview positions, plug instances, hinge pivots
- `SCALLOP_HEIGHT` derived as `socket_bottom_cut` property (exact at defaults; **needs visual review at socket_bottom_cut extremes**)
- 9 remaining constants documented with candidate formulas in `docs/CODEBASE_NOTES.md` for future visual review
- 9 inline method literals cataloged for future extraction
- Fixed Python 3.9 compatibility: `Prop` now unwraps `staticmethod` descriptors in setter
