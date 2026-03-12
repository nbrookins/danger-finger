# Parts Anatomy — Physical Design of the Danger Finger

This document describes each part of the prosthetic finger from a physical and mechanical perspective: what it does, how it connects to adjacent parts, what material it should be printed in, and which parameters most affect it. Read this before modifying any `part_*` method in `finger.py`.

---

## How the finger works

The Danger Finger is a body-powered prosthetic for people missing a finger at any phalange. The key mechanical principles:

1. **Socket** slides over the remnant finger stub (flexible material for comfort)
2. **Base** snaps into the socket via a ridged cylindrical interface
3. **Middle** connects to the base via a proximal hinge joint
4. **Tip** connects to the middle via a distal hinge joint
5. **Tipcover** (flexible) snaps onto the tip, providing a soft fingertip with fingerprint texture
6. **Linkage** runs from the base, under a bracelet on the wrist
7. **Tendon** (fishing line) threads through tunnels in all segments, attaching to the linkage
8. **Elastic cord** threads through the base, providing the return (extension) force

When the user bends their remnant finger, the base tilts forward in the socket, pulling the linkage. The linkage tension propagates through the tendon, curling the finger naturally at both hinge joints. When the remnant straightens, elastic restores the finger to its extended position.

```
                    ┌──tipcover (flexible, snaps on)
                    │
        ┌───tip─────┘    ← distal hinge (pin + plugs)
        │
    ┌───middle───┐       ← 3 struts + cross brace + bumper
    │            │
    └───base─────┘       ← proximal hinge (pin + plugs)
        │
        socket           ← slides over remnant (flexible)
        │
     ───linkage──→ bracelet on wrist
```

---

## Coordinate system (assembled, natural orientation)

In the natural/assembled coordinate system used by the CSG code:

- **Y axis**: finger length. Y=0 is the proximal hinge center. +Y toward tip, -Y toward hand.
- **X axis**: dorsal/palmar. +X is the dorsal (top/back) side of the finger.
- **Z axis**: lateral. +Z is one side, -Z the other.

`part_tip()` bakes `translate((0, intermediate_length, 0))` into its geometry, offsetting the tip by the middle segment length so it appears in the correct assembled position.

Print orientation rotates each part for optimal FDM printing (flat base, minimal supports). See `_rotate_offsets` in `finger_params.py`.

---

## Part-by-part anatomy

### Socket (`part_socket`)

**Material**: Flexible (TPU/NinjaFlex)
**Role**: Slides over the remnant finger stub; holds the base via friction-fit ridged interface.

**Key features**:
- **Tapered cylinder**: `socket_circumference_distal` (narrower, near base) to `socket_circumference_proximal` (wider, near hand). Wall thickness varies: `socket_thickness_distal`, `socket_thickness_middle`, `socket_thickness_proximal`.
- **Socket interface (outer)**: Cylindrical section at the top that mates with the base's inner interface. Has optional radial cuts (`socket_interface_cuts`) for flex grip.
- **Scallops**: Left and right side cutouts (`socket_scallop_depth_left/right`) that remove material for comfort and allow the socket to flex around the remnant. Controlled by `SCALLOP_HEIGHT` and `SCALLOP_RADIUS_ADJ`.
- **Bottom cut**: `socket_bottom_cut` removes material from the palm side of the socket (where the finger bends), controlled by `SOCKET_BOTTOM_CUT_FACTOR`.
- **Ridge rings**: Concentric ridges (`_socket_bottom` method) add grip texture inside the socket body.
- **Tendon cut**: Angled cut (`TENDON_CUT_ROTATE = -80`) near the top provides a channel for the tendon to exit toward the linkage.
- **Rotation for draft**: The socket is rotated 20 degrees during construction (`rotate((0,20,0))`) then un-rotated, creating a slight draft angle that improves insertability.

**Key parameters**: `socket_depth`, `socket_circumference_distal/proximal`, `socket_thickness_*`, `socket_bottom_cut`, `socket_scallop_depth_*`, `socket_interface_*`

**Interfaces with**: Base (via socket_interface cylinder)

---

### Base (`part_base`)

**Material**: Rigid (PLA/PETG)
**Role**: Proximal segment. Connects socket to middle via the proximal hinge. Routes tendon and elastic.

**Key features**:
- **Core**: A flanged cylinder (`_mod_core`) at the socket end that transitions into the hinge geometry.
- **Outer hinge** (`knuckle_outer`, Orient.PROXIMAL): Rounded cylinder with a pin hole, washer grooves, and a clearance cut for the mating inner hinge. The hinge tab width is `knuckle_proximal_thickness`; the overall width is `knuckle_proximal_width`.
- **Socket interface (inner)**: Ridged cylinder (`socket_interface`, Orient.INNER) that friction-fits into the socket's outer interface. Ridges (`socket_interface_ridges`) and optional flex cuts improve grip. `socket_interface_clearance` controls the fit tolerance.
- **Tendon routing**: `tendon_hole()` cuts two hulled tube channels through the base for the fishing line. The holes can be shifted upward by `knuckle_tendon_offset` to create a mechanical advantage (with a corresponding `_tendon_bulge` that adds material to accommodate the shifted hole).
- **Elastic routing**: `elastic_hole()` cuts four channels (two pairs) for the elastic return cord. They run from the base's socket end through to the hinge area.
- **Breather hole**: A cylinder cut through the body between the hinge and socket interface, allowing air escape during socket insertion.
- **Bridge/tunnel**: Tendon guide structures (`bridge()` + `make_bridge()`) that route the tendon smoothly through the hinge zone.
- **Front cut**: `_front_cut()` removes a small wedge from the front/bottom of the base for knuckle clearance during flexion.
- **Plug cuts**: Four plug socket holes (proximal left/right, distal left/right) for the hinge pin cover plugs.

**Key parameters**: `proximal_length`, `knuckle_proximal_width/thickness`, `socket_interface_*`, `knuckle_tendon_offset`, `tunnel_*`, `tendon_hole_radius/width`

**Interfaces with**: Socket (via socket_interface), Middle (via proximal hinge pin)

---

### Middle (`part_middle`)

**Material**: Rigid (PLA/PETG)
**Role**: Intermediate segment connecting base to tip. Transmits tendon force. Allows flexion at both hinges.

**Key features**:
- **Dual inner hinges** (`knuckle_inner`): One at each end (proximal and distal). Inner hinges are the "socket" side — they receive the outer hinge cylinders from the base and tip. Each has a flared inset (`knuckle_inset_border`, `knuckle_inset_depth`) that creates a channel for the tendon to pass through without binding.
- **Three struts**: Top-left, top-right, and bottom struts hull-connect the two hinges. The bottom strut is rotated by `intermediate_strut_rotate` to provide fist clearance (so the finger doesn't collide with the palm when fully curled).
- **Cross brace** (`cross_strut`): A transverse bar at the midpoint connecting the top struts for lateral rigidity. Height controlled by `knuckle_brace_height_factor`.
- **Bumper**: Optional protective shell around the middle section. `intermediate_bumper_style` selects NONE, MINIMAL, COVER, or FULL. The COVER style (`_create_cover_bumper`) wraps the struts in a thin shell via `rcubecyl` with a hollow interior. `intermediate_bumper_width` controls thickness.
- **Bridge tunnels**: When bumper style is not COVER/FULL, separate `create_bridge()` tunnels at each end guide the tendon. When COVER/FULL, the `make_bridge()` method creates integrated bridge structures.
- **Side trims**: Cylinder cuts at each end ensure the inner hinge doesn't interfere with the outer hinge's clearance zone.
- **Tendon channel**: When bumper is COVER/FULL, a tendon-shaped hull cut runs through the bumper for the fishing line.

**Key parameters**: `intermediate_length`, `intermediate_distal_height`, `intermediate_proximal_height`, `knuckle_distal/proximal_width`, `intermediate_bumper_style/width`, `knuckle_inset_*`, `intermediate_strut_rotate`, `strut_*`, `tunnel_*`

**Interfaces with**: Base (proximal hinge), Tip (distal hinge)

**Critical**: `intermediate_length` is the single most important parameter — it determines the finger's overall length and affects the Y-position of every part distal to the proximal hinge.

---

### Tip (`part_tip`)

**Material**: Rigid (PLA/PETG)
**Role**: Distal segment. Houses the peg hole for the tendon anchor. Receives the tipcover snap-fit.

**Key features**:
- **Outer hinge** (`knuckle_outer`, Orient.DISTAL): Same structure as the base hinge but at the distal end.
- **Tip core**: An `rcylinder` with `tip_radius` (derived from `tip_circumference/pi/2`) that forms the dome-shaped fingertip. This is the visual and structural terminus of the rigid finger.
- **Tip interface** (`tip_interface`): A post-and-ridge snap-fit system. A central post (`tip_interface_post_height`, `tip_interface_post_radius_`) with a circumferential ridge (`tip_interface_ridge_radius`, `tip_interface_ridge_height`) that the flexible tipcover snaps onto. The ridge has a chamfer for easier insertion.
- **Peg hole**: A tapered cylinder (`part_peg` subtracted from the tip) that serves as the tendon anchor point. The fishing line terminates here, secured by the peg. Four support cylinders (`PEG_SUPPORT_RADIUS`, `PEG_SUPPORT_TRANSLATE_Z`, `PEG_SUPPORT_SIDE_X_OFFSET`) reinforce the peg channel.
- **Bottom trim**: Removes material from the underside to improve fist clearance.
- **Fist trim**: An angled cube cut (`TIP_FIST_TRIM_ROTATE = -25`) that trims the palm side of the tip, preventing collision when the finger is fully curled.
- **Bridge/tunnel**: Same structure as the base, routing the tendon through the hinge zone.

**Key parameters**: `tip_circumference`, `distal_length`, `distal_base_length`, `knuckle_distal_width/thickness`, `tip_interface_*`, `distal_flange_height`

**Interfaces with**: Middle (distal hinge), Tipcover (snap-fit interface), Peg (tendon anchor)

**Note**: `part_tip()` applies `translate((0, intermediate_length, 0))` to the final geometry, placing it at the correct assembled position relative to the proximal hinge origin.

---

### Tipcover (`part_tipcover`)

**Material**: Flexible (TPU/NinjaFlex)
**Role**: Soft fingertip that snaps onto the tip. Provides grip, appearance, and protection.

**Key features**:
- **Shell**: A hull of a cylinder and sphere that creates the finger-shaped dome. `tipcover_thickness` controls wall thickness. The inner surface is hollowed by a slightly smaller version of the tip interface post.
- **Snap-fit interface**: The inner cavity has a matching ridge that clicks onto the tip's post, held by friction. `tip_interface_clearance` controls the gap.
- **Nail cut**: A sphere subtracted from the dorsal (top) side that creates a nail-like depression for aesthetics.
- **Fingerprints**: Concentric sphere intersections with alternating stripe cuts create a tactile fingerprint pattern. `tip_print_depth` controls ridge depth (negative inverts), `tip_print_width` controls stripe spacing, `tip_print_factor` controls sphere radius, `tip_print_offset` positions the pattern.

**Key parameters**: `tipcover_thickness`, `tip_circumference`, `tip_print_*`, `tip_interface_*`

**Interfaces with**: Tip (snap-fit)

---

### Linkage (`part_linkage`)

**Material**: Rigid (PLA/PETG)
**Role**: Connects the finger to a wrist bracelet. Transmits pull force from remnant finger flexion to tendon.

**Key features**:
- **Core bar**: An `rcylinder` resized to an oval cross-section (`linkage_width` x `linkage_height`), intersected with a cube for flat sides. Length is `linkage_length`.
- **Hook** (`link_hook`): A loop at one end that hooks onto the wrist bracelet's elastic band. Controlled by `linkage_hook_*` parameters (length, height, thickness, opening, offset, inset, rounding, end_inset).
- **Tendon hole**: A long cylinder bored through the center for the fishing line. `linkage_flat` adds width to the oval.
- **Cross holes**: `linkage_holes` evenly-spaced holes perpendicular to the tendon, connected by slits. These allow tension adjustment — the user can thread the tendon through different holes to change the effective pull distance.
- **Hull transition**: The hook and core are hull-connected for a smooth structural transition.

**Key parameters**: `linkage_length`, `linkage_width`, `linkage_height`, `linkage_hook_*`, `linkage_holes`, `linkage_hole_spacing`, `linkage_flat`

**Interfaces with**: Base (tendon runs through base tunnels to linkage), wrist bracelet (hook)

---

### Plug (`part_plug`)

**Material**: Rigid (PLA)
**Role**: Cap for the hinge pin hole. Prevents the pin from sliding out.

**Key features**:
- **Two-part cylinder**: A wider base with a ridge (`knuckle_plug_ridge`) that friction-fits into the hinge's pin hole. `knuckle_plug_radius` controls diameter; `knuckle_plug_thickness` controls depth.
- **Clearance version**: `part_plug(clearance=True)` adds `knuckle_plug_clearance` to create the mating hole in the hinge. `clearance=False` creates the actual plug.
- **Four instances**: `part_plugs()` creates four plugs at the correct positions: proximal left/right, distal left/right.

**Key parameters**: `knuckle_plug_radius`, `knuckle_plug_thickness`, `knuckle_plug_ridge`, `knuckle_plug_clearance`

**Interfaces with**: Base (2 plugs), Tip (2 plugs)

---

### Peg (`part_peg`)

**Material**: Rigid (PLA)
**Role**: Tendon anchor inserted into the tip's peg hole.

**Key features**:
- Tapered cylinder (`r1=tendon_hole_radius*2, r2=tendon_hole_radius*1.3`)
- Optionally hollow (`peg_hollow_radius`) for tying the tendon through it
- Oriented and positioned to align with the peg hole in `part_tip`

**Key parameters**: `tendon_hole_radius`, `peg_hollow_radius`, `distal_base_length`

**Interfaces with**: Tip (peg hole)

---

### Pins (`part_pins`)

**Material**: Rigid (PLA) or metal rod
**Role**: Hinge axles. One pin for proximal hinge, one for distal.

**Key features**:
- Simple cylinders at `knuckle_pin_radius` with length matching the hinge width minus plug thickness.
- Both pins are generated as a single composite STL (proximal at Y=0, distal at Y=10), which is why the web viewer skips pins (the composite cannot be correctly positioned with a single offset).

**Key parameters**: `knuckle_pin_radius`, `knuckle_proximal/distal_width`, `knuckle_plug_thickness`

**Interfaces with**: Base (proximal), Middle (both), Tip (distal), Plugs (cap the ends)

---

### Stand (`part_stand`)

**Material**: Rigid (PLA)
**Role**: Display stand for the assembled finger. Not a functional part.

**Key features**:
- Inner shape matches the socket's inner cavity (reuses `_socket_bottom_bit`), so the assembled finger sits snugly.
- Outer base is a wider rounded cylinder with "DangerFinger v5.1 2014-2026" circular text.
- `stand_depth_factor` controls how deep the stand is relative to `socket_depth`.

**Key parameters**: `stand_depth_factor`, `socket_depth`, `socket_radius_*`

**Interfaces with**: Socket (display only)

---

### Bumper (`part_bumper`)

**Material**: Flexible (TPU)
**Role**: Protective sleeve around the middle section. Separate from the bumper integrated into `part_middle` when `intermediate_bumper_style` is COVER/FULL.

**Key features**:
- A thin-walled `rcubecyl` shell that slides over the middle section's struts.
- Only generated when `intermediate_bumper_style` is not NONE.

**Key parameters**: `intermediate_bumper_width`, `intermediate_bumper_style`

**Interfaces with**: Middle (slides over)

---

## The hinge system in detail

Each hinge consists of an **outer** part (on base or tip) and an **inner** part (on middle). They interleave like a door hinge:

```
 Outer hinge (on base or tip)          Inner hinge (on middle)
 ┌──────────────────────────┐          ┌──────────────────────────┐
 │  ███░░░░░░░░░░░░░░░░███  │          │  ░░░██████████████████░░░│
 │  ███░░░░pin hole░░░░███  │          │  ░░░██████████████████░░░│
 │  ███░░░░░░░░░░░░░░░░███  │          │  ░░░██████████████████░░░│
 └──────────────────────────┘          └──────────────────────────┘
   ▲ plug                  plug ▲         ▲ inset gap           inset gap ▲
```

- **Outer** (`knuckle_outer`): Full-width rounded cylinder. Pin hole through center. Clearance cut removes a cylinder-shaped void for the inner hinge to nestle into. Washer grooves reduce friction.
- **Inner** (`knuckle_inner`): Narrower cylinder (width = `intermediate_width_[orient]`). Flanged inset (`knuckle_inset_border`, `knuckle_inset_depth`) creates tendon channels. Anchor points for struts are generated here.
- **Pin**: Simple cylinder through both, length = hinge width - 2 * plug thickness.
- **Plugs**: Cap the pin holes on each end.
- **Washers**: Built-in annular ridges on the outer hinge that reduce friction between the inner and outer hinge faces.

Critical clearances:
- `knuckle_clearance`: Gap between inner and outer hinge cylinders (radial)
- `knuckle_side_clearance`: Gap between inner hinge face and outer hinge wall (axial)
- `knuckle_plug_clearance`: Gap between plug and its hole

---

## The tendon/tunnel system

Fishing line runs from the linkage, through the base, through both hinge zones, through the middle, to the peg in the tip:

```
Linkage → tendon_hole (base) → bridge tunnel (proximal hinge zone)
  → create_bridge tunnels (middle proximal end)
  → [through middle body] →
  → create_bridge tunnels (middle distal end)
  → bridge tunnel (distal hinge zone) → peg hole (tip)
```

The tunnel system is built from `bridge()` and `bridge_anchor()` methods, which generate hull-connected anchor points at specific heights and widths. The tunnel interior is subtracted using `rcylinder` cuts.

Key tunnel parameters:
- `tunnel_height`: How far the tunnel extends above the hinge center
- `tunnel_radius`: Radius of the tunnel tube
- `tunnel_inner_height`: Extra height for the inner (middle) end
- `tunnel_inner_slant`, `tunnel_outer_slant`, `tunnel_outer_flare`: Control the tunnel's narrowing/widening as it transitions between segments
- `tunnel_inner_rounding`: Rounding on the inner tunnel edges

---

## The socket interface

The socket and base connect via a cylindrical friction-fit interface:

```
Socket (outer)                     Base (inner)
┌────────────────────────┐        ┌────────────────────────┐
│ ╔═══════════════════╗  │        │  ┌───────────────────┐ │
│ ║  ridges (outer)   ║  │  ←→   │  │ ridges (inner)    │ │
│ ║  socket_iface_rad ║  │        │  │ socket_iface_rad  │ │
│ ║  + thickness      ║  │        │  │ - clearance       │ │
│ ╚═══════════════════╝  │        │  └───────────────────┘ │
└────────────────────────┘        └────────────────────────┘
```

- `socket_interface_radius_distal/proximal`: Radius at each end (tapered)
- `socket_interface_thickness`: Wall thickness of the interface cylinder
- `socket_interface_clearance`: Gap between base (inner) and socket (outer) — negative for interference fit
- `socket_interface_ridges`: Number of vertical ridges for grip (0 disables)
- `socket_interface_ridge_width`, `_inner`, `_outer`: Ridge geometry
- `socket_interface_cuts`: Whether radial flex cuts are present (helps the interface flex for insertion)

The `socket_interface()` method generates both the inner (for base, with clearance subtracted) and outer (for socket, at full size) versions based on the `orient` parameter.

---

## Known modeling challenges and TODOs

These are extracted from code comments and represent the key areas where future parametric work is needed:

### Tier 1 — Hardcoded values that should be derived
- `ANCHOR_OFFSET_DISTAL = -0.485` — should derive from `strut_height_ratio` and `knuckle_clearance`
- `SCALLOP_HEIGHT = 9` — may be derivable from `socket_bottom_cut`
- `PEG_SUPPORT_*` constants — should derive from `tendon_hole_radius` and `distal_base_length`
- `TIP_CORE_RESIZE_INSET = 2` — should be proportional to `tip_radius`
- `breather_radius_factor`, `breather_height`, `breather_translate_y` — should derive from base dimensions

### Tier 2 — Features that need parameterization
- Cross strut width (currently hardcoded in `cross_strut`)
- Bridge height (hardcoded; TODO comments say "make configurable")
- Socket texture / cuts (separate from interface ridges)
- Fist clearance geometry (multiple HACK comments)
- Bumper parametrics (COVER style has several hardcoded dimensions)

### Tier 3 — Structural improvements
- Snap knuckles instead of pins (mentioned in TODO at top of finger.py)
- Width resize for tip and base (TODO 3 in multiple places)
- Better fist bottom cut for tipcover
- Separate socket cut config vs base cut config
- Plug rotation for left vs right hand
