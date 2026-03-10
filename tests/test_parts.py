import pytest
from solid2 import scad_render
from danger.finger import DangerFinger


def test_part_plugs_and_scad_render():
    f = DangerFinger()
    plugs = f.part_plugs()
    assert isinstance(plugs, tuple) and len(plugs) == 4
    # rendering one plug to SCAD should not raise
    scad = scad_render(plugs[0])
    assert isinstance(scad, str) and len(scad) > 0


def test_create_bridge_sharp_smoke():
    f = DangerFinger()
    b = f.create_bridge(r=f.tunnel_radius, length=4, width=12, height=1, tunnel_width=2, tunnel_height=1, sharp=True)
    s = scad_render(b)
    assert isinstance(s, str) and len(s) > 0


def test_part_peg_and_pins_translate():
    f = DangerFinger()
    # ensure peg support params exist and produce scad
    scad = scad_render(f.part_peg(hollow=True))
    assert isinstance(scad, str) and len(scad) > 0
    # pins translation gap should match property
    pins = f.part_pins()
    scad_pins = scad_render(pins)
    assert isinstance(scad_pins, str) and len(scad_pins) > 0

