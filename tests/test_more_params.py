import pytest
from danger.finger import DangerFinger


def test_peg_hollow_radius_is_live_model_param():
    finger = DangerFinger()
    assert isinstance(finger.peg_hollow_radius, (int, float))
    assert finger.peg_hollow_radius == pytest.approx(0.5)
    assert finger.peg_hollow_radius <= finger.tendon_hole_radius * 2.0


def test_part_peg_and_pins_translate_smoke():
    from solid2 import scad_render

    finger = DangerFinger()
    scad = scad_render(finger.part_peg(hollow=True))
    assert isinstance(scad, str) and len(scad) > 0
    pins = finger.part_pins()
    scad_pins = scad_render(pins)
    assert isinstance(scad_pins, str) and len(scad_pins) > 0
