import math
import pytest
from danger.finger_params import DangerFingerParams
from danger.constants import Orient
from solid2 import scad_render


def test_proto_shell_sphere_radius_default_derived():
    p = DangerFingerParams()
    # set a known tip circumference so tip_radius is predictable
    p.tip_circumference = 100.0
    expected = max(1, p.tip_radius * 0.7)
    assert p.proto_shell_sphere_radius == pytest.approx(expected)


def test_proto_shell_sphere_radius_override():
    p = DangerFingerParams()
    p.proto_shell_sphere_radius = 9.0
    assert p.proto_shell_sphere_radius == 9.0


def test_bridge_ledge_default_and_override():
    p = DangerFingerParams()
    expected = max(0.5, p.tunnel_radius * 0.9)
    assert p.bridge_ledge == pytest.approx(expected)
    p.bridge_ledge = 2.25
    assert p.bridge_ledge == pytest.approx(2.25)


def test_cut_fist_radius_derived():
    p = DangerFingerParams()
    expected = max(0.01, p.intermediate_width_[Orient.PROXIMAL] * 0.02)
    assert p.cut_fist_radius_offset == pytest.approx(expected)


def test_breather_and_bridge_defaults():
    p = DangerFingerParams()
    assert p.breather_radius_factor == pytest.approx(0.2)
    assert p.breather_height == pytest.approx(20)
    assert p.bridge_cut_translate_x == pytest.approx(0.2)
    assert p.bridge_cut_translate_y == pytest.approx(-2.0)


def test_peg_defaults_and_hollow():
    from danger.finger import DangerFinger
    f = DangerFinger()
    assert f.peg_hollow_radius == pytest.approx(0.5)
    s_no_hollow = scad_render(f.part_peg(hollow=False))
    s_hollow = scad_render(f.part_peg(hollow=True))
    assert s_no_hollow != s_hollow


def test_breather_and_bridge_defaults():
    p = DangerFingerParams()
    assert p.breather_radius_factor == pytest.approx(0.2)
    assert p.breather_height == pytest.approx(20)
    assert p.bridge_cut_translate_x == pytest.approx(0.2)
    assert p.bridge_cut_translate_y == pytest.approx(-2.0)


def test_peg_defaults_and_hollow():
    from danger.finger import DangerFinger
    f = DangerFinger()
    assert f.peg_hollow_radius == pytest.approx(0.5)
    s_no_hollow = scad_render(f.part_peg(hollow=False))
    s_hollow = scad_render(f.part_peg(hollow=True))
    assert s_no_hollow != s_hollow

