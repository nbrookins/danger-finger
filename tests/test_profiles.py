import inspect
import pytest

from danger.Params import Params, Prop
from danger.constants import RenderQuality
from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams
from danger.geometry_checks import check_no_degenerate
from danger.tools import iterable
from tests.profiles import COMMON_PLUS_FIT_FIELDS, PROFILES, PROFILE_ORDER


def _props():
    return {
        name: prop
        for name, prop in inspect.getmembers(DangerFingerParams)
        if isinstance(prop, Prop)
    }


def _build_profile(profile_name):
    """Build a DangerFinger from a named profile, returns the finger instance."""
    config = PROFILES[profile_name]
    finger = DangerFinger()
    Params.apply_config(finger, config)
    finger.render_quality = RenderQuality.STUPIDFAST
    finger.build()
    return finger


def test_profiles_only_use_known_common_plus_fit_fields():
    props = _props()
    for profile_name, config in PROFILES.items():
        assert set(config).issubset(COMMON_PLUS_FIT_FIELDS), profile_name
        for key in config:
            assert key in props, f"{profile_name}: unknown field {key}"


def test_profiles_respect_declared_prop_ranges():
    props = _props()
    for profile_name, config in PROFILES.items():
        for key, value in config.items():
            prop = props[key]
            if prop.minimum is not None:
                assert value >= prop.minimum, f"{profile_name}: {key} below min"
            if prop.maximum is not None:
                assert value <= prop.maximum, f"{profile_name}: {key} above max"


def test_profiles_build_without_exception():
    for profile_name, config in PROFILES.items():
        finger = DangerFinger()
        Params.apply_config(finger, config)
        finger.render_quality = RenderQuality.STUPIDFAST
        finger.build()
        assert finger.models, f"{profile_name}: build produced no models"


# --- Pass 2: profile validation, per-part checks, preview position consistency ---


GEOMETRY_PARTS = ["base", "middle", "tip", "tipcover", "socket", "linkage", "peg", "stand"]


@pytest.mark.parametrize("profile_name", PROFILE_ORDER)
def test_profile_validate_params(profile_name):
    """Every profile should pass validate_params (no constraint violations)."""
    config = PROFILES[profile_name]
    finger = DangerFinger()
    Params.apply_config(finger, config)
    warnings = finger.validate_params()
    assert warnings == [], f"{profile_name} has validation warnings: {warnings}"


@pytest.mark.parametrize("profile_name", PROFILE_ORDER)
def test_profile_all_parts_non_degenerate(profile_name):
    """Every profile should produce non-degenerate SCAD for every geometry part."""
    finger = _build_profile(profile_name)
    for part_name in GEOMETRY_PARTS:
        model = finger.models.get(part_name)
        if model is None:
            continue
        scad_str = model[0].scad if iterable(model) else model.scad
        passed, msg = check_no_degenerate(scad_str)
        assert passed, f"{profile_name}/{part_name}: {msg}"


@pytest.mark.parametrize("profile_name", PROFILE_ORDER)
def test_profile_preview_positions_reasonable(profile_name):
    """Dynamic preview positions should produce finite, reasonable values."""
    config = PROFILES[profile_name]
    finger = DangerFinger()
    Params.apply_config(finger, config)
    positions = finger.compute_preview_positions()
    for part_name, pos in positions.items():
        for axis_idx, axis_name in enumerate("xyz"):
            val = pos[axis_idx]
            assert isinstance(val, (int, float)), f"{profile_name}/{part_name}/{axis_name}: not numeric ({val})"
            assert abs(val) < 200, f"{profile_name}/{part_name}/{axis_name}: out of range ({val})"


@pytest.mark.parametrize("profile_name", PROFILE_ORDER)
def test_profile_preview_plugs_reasonable(profile_name):
    """Dynamic plug instances should produce finite, reasonable positions."""
    config = PROFILES[profile_name]
    finger = DangerFinger()
    Params.apply_config(finger, config)
    plugs = finger.compute_preview_plug_instances()
    assert len(plugs) == 4, f"{profile_name}: expected 4 plug instances, got {len(plugs)}"
    for i, plug in enumerate(plugs):
        pos = plug["position"]
        for axis_idx, axis_name in enumerate("xyz"):
            val = pos[axis_idx]
            assert isinstance(val, (int, float)), f"{profile_name}/plug[{i}]/{axis_name}: not numeric"
            assert abs(val) < 100, f"{profile_name}/plug[{i}]/{axis_name}: out of range ({val})"


@pytest.mark.parametrize("profile_name", PROFILE_ORDER)
def test_profile_hinge_pivots_reasonable(profile_name):
    """Dynamic hinge pivots should be at y=0 (proximal) and y=intermediate_length (distal)."""
    config = PROFILES[profile_name]
    finger = DangerFinger()
    Params.apply_config(finger, config)
    pivots = finger.compute_hinge_pivots()
    assert pivots["proximal"][1] == 0, f"{profile_name}: proximal pivot Y != 0"
    assert pivots["distal"][1] == pytest.approx(finger.intermediate_length, abs=0.2), \
        f"{profile_name}: distal pivot Y ({pivots['distal'][1]}) != intermediate_length ({finger.intermediate_length})"
