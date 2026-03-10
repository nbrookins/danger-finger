import pytest
from danger.finger_params import DangerFingerParams


def test_peg_and_pins_translate_defaults():
    p = DangerFingerParams()
    # peg_hollow_radius should be less than or equal to peg_support_radius
    assert p.peg_hollow_radius <= p.peg_support_radius
    # pins_translate_y should be numeric
    assert isinstance(p.pins_translate_y, (int, float))


def test_part_peg_and_pins_translate_smoke():
    from danger.finger import DangerFinger
    from solid2 import scad_render

    f = DangerFinger()
    # ensure peg support params exist and produce scad
    scad = scad_render(f.part_peg(hollow=True))
    assert isinstance(scad, str) and len(scad) > 0
    # pins rendering
    pins = f.part_pins()
    scad_pins = scad_render(pins)
    assert isinstance(scad_pins, str) and len(scad_pins) > 0
