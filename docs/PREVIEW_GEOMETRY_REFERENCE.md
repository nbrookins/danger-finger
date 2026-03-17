# Preview Geometry Reference

Canonical reference for 3D preview part positioning. Consult before changing any offsets.

## Coordinate system

- **Y** = finger long axis (proximal hinge = Y≈0, distal hinge = Y≈int_len)
- **X** = forward/back (positive = toward palm/front, negative = toward back of hand)
- **Z** = left/right (lateral axis, hinge pin direction)

## Current offsets (default params, int_len=24)

| Part     | X   | Y    | Z   | Notes |
|----------|-----|------|-----|-------|
| socket   | 0   | -26  | 0   | Large cylindrical socket, wraps around base bottom |
| base     | 0   | -4   | 0   | Proximal hinge at top (Y≈0) |
| middle   | 0   | 11   | 0   | Spans proximal→distal hinge, struts + cross-members |
| tip      | 1   | 26   | 0   | Distal hinge at bottom (Y≈24), X=1 for slight forward offset |
| tipcover | 0   | 38   | 0   | Dome cap on top of tip |
| linkage  | 0   | -3   | 20  | Tendon routing channel, spans full finger on Z side |
| stand    | 0   | -45  | 0   | Display stand, hidden by default |
| bumper   | 0.5 | 11   | 0   | TPU ring around middle section; X tested: 0=too back, 0.5=flush, 1=tiny protrude back, 2=too forward |
| plug     | inst | inst | inst | 4 instances at hinge faces (see below) |

## Plug instances

| Instance       | X | Y  | Z     | Rotation    |
|----------------|---|-----|-------|-------------|
| Proximal left  | 0 | 0   | -8.6  | (0, 0, 0)   |
| Proximal right | 0 | 0   | 8.6   | (0, 180, 0) |
| Distal left    | 0 | 24  | -7.4  | (0, 0, 0)   |
| Distal right   | 0 | 24  | 7.4   | (0, 180, 0) |

Plugs sit at Y=0 (proximal hinge) and Y=int_len (distal hinge). No Y nudge.

## SCAD-derived bbox centers (ground truth for default params)

Computed by applying inverse-print-rotation to native STL vertices + SCAD "all" offsets:

| Part     | SCAD X | SCAD Y | SCAD Z |
|----------|--------|--------|--------|
| socket   | 0.0    | -25.9  | 0.0    |
| base     | 0.5    | -3.9   | 0.0    |
| middle   | 1.0    | 11.6   | 0.0    |
| tip      | 1.2    | 26.3   | 0.0    |
| tipcover | 0.0    | 39.0   | 0.0    |
| linkage  | 0.1    | -3.1   | 20.0   |
| stand    | 0.0    | -45.1  | 0.0    |
| bumper   | 0.0    | 0.0    | 0.0    |

Note: bumper SCAD center is (0,0,0) because in SCAD it's at the proximal hinge origin.
In the web viewer, bumper must be at middle_y to wrap around the struts after geometry.center().

## Alignment rules

1. **Bumper X must match middle X.** Both wrap the same strut section. If middle moves on X, bumper follows.
2. **Tip X=1** gives a slight forward lean that matches the hinge geometry. Reducing to 0 makes the tip appear recessed.
3. **Hinge overlaps (5-10mm) are natural.** Fork/socket geometry interleaves at each joint. Don't try to eliminate.
4. **Tipcover sits flush on tip.** The gap between tip Y and tipcover Y should be ~12mm (half of each part's Y extent).
5. **Socket/base overlap is expected.** Socket wraps around the base; the top of socket extends up to near the proximal hinge.

## Rotated bounding box dimensions (after center + preview rotation)

| Part     | Y half-height | Total Y extent |
|----------|---------------|----------------|
| socket   | 20.4          | 40.9           |
| base     | 9.4           | 18.8           |
| middle   | 17.1          | 34.2           |
| tip      | 7.1           | 14.2           |
| tipcover | 9.0           | 18.0           |
| bumper   | 1.8           | 3.5            |
| stand    | 18.1          | 36.3           |
| linkage  | 38.1          | 76.1           |
| plug     | 3.2           | 6.4            |

## Change log

| Date       | Part(s)   | Change | Reason |
|------------|-----------|--------|--------|
| 2026-03-17 | all       | Derived from SCAD part_all | Replace manual guesses with measured values |
| 2026-03-17 | plugs     | Removed +1.5mm Y nudge | Plugs were sitting above hinge holes |
| 2026-03-17 | middle    | X: 1→0, Y: 12→11 | X protrusion visible from side; gap with base |
| 2026-03-17 | tip       | Y: 27→26 | Over-correction squeezed tip between middle and cover |
| 2026-03-17 | tipcover  | Y: 39→38 | Slight gap with tip |
| 2026-03-17 | bumper    | X: 2→0→1→0.5 | Tested from back view: X=2 protrudes forward, X=0 protrudes back, X=1 tiny back protrude, X=0.5 flush |
