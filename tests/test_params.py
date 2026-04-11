import pytest
from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams
from danger.constants import Orient
from solid2 import scad_render


def test_tip_radius_default_derived():
    p = DangerFingerParams()
    p.tip_circumference = 100.0
    assert p.tip_radius == pytest.approx(p.tip_circumference / 3.141592653589793 / 2)


def test_tunnel_inner_width_depends_on_tunnel_radius():
    p = DangerFingerParams()
    p.tunnel_radius = 2.0
    expected = p.intermediate_width_[Orient.PROXIMAL] - p.strut_width * 2 + p.tunnel_radius / 2
    assert p.tunnel_inner_width_[Orient.PROXIMAL] == pytest.approx(expected)


def test_compute_preview_positions_track_length():
    p = DangerFingerParams()
    p.intermediate_length = 18
    short_positions = p.compute_preview_positions()
    p.intermediate_length = 28
    long_positions = p.compute_preview_positions()
    assert long_positions["middle"][1] > short_positions["middle"][1]
    assert long_positions["tip"][1] > short_positions["tip"][1]
    assert long_positions["tipcover"][1] > short_positions["tipcover"][1]


def test_compute_preview_plug_instances_track_knuckle_widths():
    p = DangerFingerParams()
    p.knuckle_proximal_width = 20
    p.knuckle_distal_width = 16
    plugs = p.compute_preview_plug_instances()
    assert plugs[0]["position"][2] == pytest.approx(-(p.knuckle_proximal_width / 2 - p.knuckle_plug_thickness / 2) - 0.01)
    assert plugs[2]["position"][2] == pytest.approx(-(p.knuckle_distal_width / 2 - p.knuckle_plug_thickness / 2))


def test_peg_defaults_and_hollow():
    f = DangerFinger()
    assert f.peg_hollow_radius == pytest.approx(0.5)
    s_no_hollow = scad_render(f.part_peg(hollow=False))
    s_hollow = scad_render(f.part_peg(hollow=True))
    assert s_no_hollow != s_hollow

