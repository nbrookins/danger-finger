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
from danger.Params import Prop
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


def _build_scad(config, part_name="middle"):
    """Build SCAD for a single part with given config overrides."""
    finger = DangerFinger()
    for k, v in config.items():
        try:
            setattr(finger, k, v)
        except Exception:
            pass
    finger.render_quality = RenderQuality.STUPIDFAST
    finger.build()
    model = finger.models.get(part_name)
    if model is None:
        return None
    # model.scad is the rendered SCAD string (set by build())
    if iterable(model):
        return model[0].scad
    return model.scad


SWEEPABLE = _get_sweepable_params()


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
