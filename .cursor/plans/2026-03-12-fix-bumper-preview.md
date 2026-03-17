# Fix Bumper Preview Display & Toggle Order

**Date**: 2026-03-12  
**Status**: completed

## Goal
Fix the bumper part so it's visible in the 3D preview with correct orientation, and reorder the Parts toggle checkboxes so bumper appears before stand.

## Steps
1. Reorder PARTS list in generate_static.py and generate_default_stls.py to put bumper before stand
2. Diagnose why bumper was invisible — wrong preview rotation `(0, -90, -140)` (copied from middle) didn't account for bumper's different native SCAD orientation
3. Empirically test 15+ rotation candidates using Playwright route interception to modify config-bootstrap.js without redeploying
4. Settle on `(90, 0, 0)` as correct bumper preview rotation
5. Regenerate static files and deploy to S3/CloudFront

## Key decisions
- Bumper rotation `(90, 0, 0)`: The standalone bumper STL from `part_bumper()` has no pre-rotation, unlike the middle section which applies various internal rotations during construction. The `(0, -90, -140)` rotation that works for middle doesn't work for bumper. Empirical testing with Playwright route interception was faster than geometric analysis.
- Used Playwright `page.route()` to intercept and modify `config-bootstrap.js` responses in-flight, allowing rapid rotation testing without redeploying each candidate.

## Files affected
- `danger/finger_params.py` — changed bumper preview rotation from `(0, -90, -140)` to `(90, 0, 0)`
- `scripts/generate_static.py` — reordered PARTS list: bumper before stand
- `scripts/generate_default_stls.py` — same reorder for consistency
- `web/static/config-bootstrap.js` — regenerated with new rotation and order

## Outcome
Toggle order fixed: Tip, Base, Linkage, Middle, Tipcover, Socket, Plug, Bumper, Stand.

Bumper rotation: ended at `(0, 0, 0)` — the same value it started at. The rotation was never wrong; the issue was always a position offset. Multiple deploy cycles were wasted changing rotation values before recognizing this. See lesson learned below.

Bumper position: shifted Y from `middle_y` to `middle_y + 2` (12→14 at defaults) to clear the middle section's cross-strut.

## Lesson learned
The original user report was "bumper is off a little on one axis" — a position issue. The agent incorrectly interpreted this as a rotation problem and spent 10+ iterations testing rotation values, eventually returning to the original. The fix was always a 2mm Y position shift. Rule created: `.cursor/rules/visual-spatial-fixes-are-empirical.mdc`.
