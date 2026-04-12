#!/usr/bin/env python3
"""Parameter sweep tests: verify all params produce valid SCAD at boundary values."""
import inspect
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams
from danger.constants import RenderQuality, FingerPart
from danger.Params import Prop, Params
from danger.geometry_checks import check_no_degenerate
from danger.tools import iterable
from solid2 import scad_render


def _get_sweepable_params():
    """Return list of (name, prop) for numeric Prop params with min and max."""
    params = []
    for name, prop in inspect.getmembers(DangerFingerParams):
        if name.startswith("_"):
            continue
        if isinstance(prop, Prop) and prop.minimum is not None and prop.maximum is not None:
            if isinstance(prop.default, (int, float)):
                params.append((name, prop))
    return params


def _sweep_values(prop, steps=5):
    """Generate sweep values from min to max."""
    minv, maxv = prop.minimum, prop.maximum
    if steps <= 1:
        return [prop.default]
    step = (maxv - minv) / (steps - 1)
    return [round(minv + i * step, 6) for i in range(steps)]


def _build_finger(config):
    """Build a DangerFinger with config overrides, returns the finger instance."""
    finger = DangerFinger()
    for k, v in config.items():
        try:
            setattr(finger, k, v)
        except Exception:
            pass
    finger.render_quality = RenderQuality.STUPIDFAST
    finger.build()
    return finger


def _build_scad(config, part_name="middle"):
    """Build SCAD for a single part with given config overrides."""
    finger = _build_finger(config)
    model = finger.models.get(part_name)
    if model is None:
        return None
    if iterable(model):
        return model[0].scad
    return model.scad


SWEEPABLE = _get_sweepable_params()

# Parts that have dedicated part_*() methods producing geometry
GEOMETRY_PARTS = ["base", "middle", "tip", "tipcover", "socket", "linkage", "peg", "stand"]


@pytest.mark.parametrize("param_name,prop", SWEEPABLE, ids=[p[0] for p in SWEEPABLE])
def test_param_boundaries(param_name, prop):
    """Test that min and max values produce non-degenerate SCAD for the middle part."""
    for val in [prop.minimum, prop.maximum]:
        config = {param_name: float(val)}
        scad = _build_scad(config, part_name="middle")
        if scad is None:
            pytest.skip(f"{param_name}={val} produced no SCAD for 'middle'")
        passed, msg = check_no_degenerate(scad)
        assert passed, f"{param_name}={val}: {msg}"


@pytest.mark.parametrize("param_name,prop", SWEEPABLE, ids=[p[0] for p in SWEEPABLE])
def test_param_sweep_no_exception(param_name, prop):
    """Test that sweeping a param from min to max does not raise exceptions."""
    for val in _sweep_values(prop, steps=3):
        config = {param_name: float(val)}
        try:
            _build_scad(config, part_name="middle")
        except Exception as e:
            pytest.fail(f"{param_name}={val} raised: {e}")


def test_validate_params_default():
    """Default params should produce no validation warnings."""
    finger = DangerFinger()
    warnings = finger.validate_params()
    assert warnings == [], f"Default params have warnings: {warnings}"


# --- Pass 2: all-parts sweep, interaction tests, profile validation ---


@pytest.mark.parametrize("part_name", GEOMETRY_PARTS)
def test_default_all_parts_non_degenerate(part_name):
    """Default params should produce non-degenerate SCAD for every part."""
    scad = _build_scad({}, part_name=part_name)
    if scad is None:
        pytest.skip(f"No SCAD for '{part_name}' at defaults")
    passed, msg = check_no_degenerate(scad)
    assert passed, f"{part_name} at defaults: {msg}"


@pytest.mark.parametrize("part_name", GEOMETRY_PARTS)
def test_all_parts_build_at_boundaries(part_name):
    """Build every part with each sweepable param at min and max — no exceptions."""
    for param_name, prop in SWEEPABLE:
        for val in [prop.minimum, prop.maximum]:
            config = {param_name: float(val)}
            try:
                scad = _build_scad(config, part_name=part_name)
            except Exception as e:
                pytest.fail(f"{part_name}: {param_name}={val} raised: {e}")


# Known-dangerous param pairs from the cascade table in parametric-consistency rule
INTERACTION_PAIRS = [
    ("intermediate_length", "knuckle_distal_width"),
    ("knuckle_proximal_width", "strut_width"),
    ("knuckle_distal_width", "knuckle_distal_thickness"),
    ("tip_circumference", "tipcover_thickness"),
    ("tip_circumference", "tip_interface_ridge_radius"),
    ("socket_interface_clearance", "socket_interface_thickness"),
    ("tunnel_height", "tunnel_radius"),
    ("intermediate_distal_height", "knuckle_plug_radius"),
    ("socket_circumference_distal", "socket_circumference_proximal"),
    ("distal_base_length", "distal_length"),
]


@pytest.mark.parametrize("param_a,param_b", INTERACTION_PAIRS,
                         ids=[f"{a}+{b}" for a, b in INTERACTION_PAIRS])
def test_param_interaction_no_exception(param_a, param_b):
    """Pairs of params that are known to interact: sweep both to extremes simultaneously."""
    props = {name: prop for name, prop in inspect.getmembers(DangerFingerParams) if isinstance(prop, Prop)}
    prop_a = props.get(param_a)
    prop_b = props.get(param_b)
    if prop_a is None or prop_b is None:
        pytest.skip(f"Missing prop: {param_a if prop_a is None else param_b}")
    if not isinstance(prop_a.default, (int, float)) or not isinstance(prop_b.default, (int, float)):
        pytest.skip(f"Non-numeric defaults")

    corners = [
        (prop_a.minimum, prop_b.minimum),
        (prop_a.minimum, prop_b.maximum),
        (prop_a.maximum, prop_b.minimum),
        (prop_a.maximum, prop_b.maximum),
    ]
    for val_a, val_b in corners:
        if val_a is None or val_b is None:
            continue
        config = {param_a: float(val_a), param_b: float(val_b)}
        try:
            _build_finger(config)
        except Exception as e:
            pytest.fail(f"{param_a}={val_a}, {param_b}={val_b} raised: {e}")


@pytest.mark.parametrize("param_a,param_b", INTERACTION_PAIRS,
                         ids=[f"{a}+{b}" for a, b in INTERACTION_PAIRS])
def test_param_interaction_validate(param_a, param_b):
    """Pairs of interacting params: validate_params should not crash at extremes."""
    props = {name: prop for name, prop in inspect.getmembers(DangerFingerParams) if isinstance(prop, Prop)}
    prop_a = props.get(param_a)
    prop_b = props.get(param_b)
    if prop_a is None or prop_b is None:
        pytest.skip(f"Missing prop")
    if not isinstance(prop_a.default, (int, float)) or not isinstance(prop_b.default, (int, float)):
        pytest.skip(f"Non-numeric defaults")

    corners = [
        (prop_a.minimum, prop_b.minimum),
        (prop_a.minimum, prop_b.maximum),
        (prop_a.maximum, prop_b.minimum),
        (prop_a.maximum, prop_b.maximum),
    ]
    for val_a, val_b in corners:
        if val_a is None or val_b is None:
            continue
        finger = DangerFinger()
        try:
            setattr(finger, param_a, float(val_a))
            setattr(finger, param_b, float(val_b))
        except Exception:
            continue
        warnings = finger.validate_params()
        assert isinstance(warnings, list), f"validate_params returned non-list"
