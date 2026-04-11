"""Geometric assertion helpers for validating parametric formulas under param sweeps."""

import struct
import os
import subprocess
import tempfile

# Geometry keywords that indicate non-trivial SCAD output
_GEOMETRY_KEYWORDS = frozenset(
    ('cylinder', 'cube', 'sphere', 'hull', 'polyhedron', 'linear_extrude',
     'rotate_extrude', 'union', 'difference', 'intersection', 'minkowski')
)


def bbox_from_stl(stl_path):
    """Extract bounding box from a binary STL file.
    Returns ((min_x, min_y, min_z), (max_x, max_y, max_z)) or None if file is invalid."""
    try:
        with open(stl_path, 'rb') as f:
            header = f.read(80)
            if len(header) < 80:
                return None
            count_bytes = f.read(4)
            if len(count_bytes) < 4:
                return None
            num_triangles = struct.unpack('<I', count_bytes)[0]
            min_xyz = [float('inf')] * 3
            max_xyz = [float('-inf')] * 3
            for _ in range(num_triangles):
                # 12 bytes normal (3 floats), 3 vertices * 12 bytes each, 2 bytes attribute
                tri_data = f.read(12 + 3 * 12 + 2)
                if len(tri_data) < 50:
                    return None
                # Skip normal, read vertices
                for i in range(3):
                    v = struct.unpack_from('<fff', tri_data, 12 + i * 12)
                    for j in range(3):
                        min_xyz[j] = min(min_xyz[j], v[j])
                        max_xyz[j] = max(max_xyz[j], v[j])
        return ((min_xyz[0], min_xyz[1], min_xyz[2]), (max_xyz[0], max_xyz[1], max_xyz[2]))
    except (OSError, struct.error, ValueError):
        return None


def bbox_center(bbox):
    """Return the center point of a bounding box."""
    if bbox is None:
        return None
    ((mx, my, mz), (Mx, My, Mz)) = bbox
    return ((mx + Mx) / 2, (my + My) / 2, (mz + Mz) / 2)


def bbox_dimensions(bbox):
    """Return (width_x, height_y, depth_z) of a bounding box."""
    if bbox is None:
        return None
    ((mx, my, mz), (Mx, My, Mz)) = bbox
    return (Mx - mx, My - my, Mz - mz)


def check_zero_dimension(dims, min_dimension=0.1):
    """Fail when any bbox axis is effectively collapsed."""
    if dims is None:
        return (False, "No bbox dimensions available")
    bad_axes = []
    for axis_name, value in zip(("x", "y", "z"), dims):
        if value < min_dimension:
            bad_axes.append("%s=%.4f" % (axis_name, value))
    if bad_axes:
        return (False, "Collapsed dimension(s): %s" % ", ".join(bad_axes))
    return (True, "OK")


def check_reasonable_size(dims, min_dimension=1.0, max_dimension=200.0):
    """Fail when any bbox axis is implausibly small or large for this model."""
    if dims is None:
        return (False, "No bbox dimensions available")
    issues = []
    for axis_name, value in zip(("x", "y", "z"), dims):
        if value < min_dimension:
            issues.append("%s too small (%.4f < %.4f)" % (axis_name, value, min_dimension))
        elif value > max_dimension:
            issues.append("%s too large (%.4f > %.4f)" % (axis_name, value, max_dimension))
    if issues:
        return (False, "; ".join(issues))
    return (True, "OK")


def check_no_degenerate(scad_str, min_scad_length=100):
    """Verify SCAD output is non-trivial.
    Returns (passed: bool, message: str)."""
    if not isinstance(scad_str, str):
        return (False, "scad_str must be a string")
    if len(scad_str) < min_scad_length:
        return (False, "SCAD output too short (%d < %d)" % (len(scad_str), min_scad_length))
    lower = scad_str.lower()
    if not any(kw in lower for kw in _GEOMETRY_KEYWORDS):
        return (False, "SCAD output lacks geometry keywords (cylinder, cube, sphere, hull, etc.)")
    return (True, "OK")


def check_proportional_scaling(build_fn, param_name, param_values, expected_axis, finger_cls=None):
    """Sweep a param and verify bounding box scales monotonically on expected_axis.

    Args:
        build_fn: callable(finger_instance) -> SolidPython2 object (the part builder)
        param_name: name of the param to sweep
        param_values: list of values to test (should be monotonically increasing)
        expected_axis: 0=X, 1=Y, 2=Z - which bbox dimension should grow
        finger_cls: the DangerFinger class (imported lazily to avoid circular imports)

    Returns (passed: bool, details: list[dict]) where each dict has {value, bbox, dimension}.
    """
    if finger_cls is None:
        from danger.finger import DangerFinger
        finger_cls = DangerFinger

    from solid2 import scad_render
    from danger.Scad_Renderer import Scad_Renderer

    details = []
    prev_dim = None

    with tempfile.TemporaryDirectory() as tmpdir:
        renderer = Scad_Renderer()
        for val in param_values:
            finger = finger_cls()
            setattr(finger, param_name, val)
            try:
                obj = build_fn(finger)
            except Exception as e:
                return (False, details + [{"value": val, "error": str(e)}])
            scad_str = scad_render(obj)
            scad_path = os.path.join(tmpdir, "part_%s.scad" % str(val).replace(".", "_"))
            with open(scad_path, 'w') as f:
                f.write(scad_str)
            stl_path = scad_path.replace(".scad", ".stl")
            try:
                renderer.scad_to_stl(scad_path, stl_path)
            except Exception as e:
                return (False, details + [{"value": val, "error": "scad_to_stl: %s" % e}])
            bbox = bbox_from_stl(stl_path)
            if bbox is None:
                return (False, details + [{"value": val, "error": "bbox_from_stl failed"}])
            dims = bbox_dimensions(bbox)
            dim_val = dims[expected_axis]
            details.append({"value": val, "bbox": bbox, "dimension": dim_val})
            if prev_dim is not None and dim_val <= prev_dim:
                return (False, details)
            prev_dim = dim_val

    return (True, details)


def check_clearance_stl(stl_path_a, stl_path_b, max_overlap_mm=0.5):
    """Check that two STL parts don't overlap by more than max_overlap_mm.
    Uses bounding box overlap as a fast approximation.
    Returns (passed: bool, overlap_mm: float, message: str)."""
    bbox_a = bbox_from_stl(stl_path_a)
    bbox_b = bbox_from_stl(stl_path_b)
    if bbox_a is None:
        return (False, 0.0, "Invalid STL: %s" % stl_path_a)
    if bbox_b is None:
        return (False, 0.0, "Invalid STL: %s" % stl_path_b)

    (amin, amax) = bbox_a
    (bmin, bmax) = bbox_b

    overlap_x = max(0, min(amax[0], bmax[0]) - max(amin[0], bmin[0]))
    overlap_y = max(0, min(amax[1], bmax[1]) - max(amin[1], bmin[1]))
    overlap_z = max(0, min(amax[2], bmax[2]) - max(amin[2], bmin[2]))

    if overlap_x <= 0 or overlap_y <= 0 or overlap_z <= 0:
        return (True, 0.0, "No overlap")

    overlap_mm = max(overlap_x, overlap_y, overlap_z)
    passed = overlap_mm <= max_overlap_mm
    msg = "Overlap %.3f mm (max allowed %.3f)" % (overlap_mm, max_overlap_mm)
    return (passed, overlap_mm, msg)


def check_bbox_ratio(stl_path, expected_ratios, tolerance=0.15):
    """Check that bbox dimension ratios are within tolerance of expected.
    expected_ratios: dict like {"xy": 0.5, "xz": 1.0} meaning width/height ≈ 0.5, width/depth ≈ 1.0
    Returns (passed: bool, actual_ratios: dict, message: str)."""
    bbox = bbox_from_stl(stl_path)
    if bbox is None:
        return (False, {}, "Invalid STL: %s" % stl_path)

    dims = bbox_dimensions(bbox)
    w, h, d = dims[0], dims[1], dims[2]

    axis_map = {"x": 0, "y": 1, "z": 2}
    dim_map = {0: "x", 1: "y", 2: "z"}

    actual_ratios = {}
    all_passed = True
    msgs = []

    for key, expected in expected_ratios.items():
        if len(key) != 2 or key[0] not in axis_map or key[1] not in axis_map:
            continue
        i, j = axis_map[key[0]], axis_map[key[1]]
        denom = dims[j]
        if denom == 0:
            actual_ratios[key] = float('inf') if dims[i] else 0.0
            all_passed = False
            msgs.append("%s: division by zero" % key)
            continue
        actual = dims[i] / denom
        actual_ratios[key] = actual
        diff = abs(actual - expected)
        if diff > tolerance:
            all_passed = False
            msgs.append("%s: got %.3f, expected %.3f (tol %.3f)" % (key, actual, expected, tolerance))

    msg = "; ".join(msgs) if msgs else "OK"
    return (all_passed, actual_ratios, msg)
