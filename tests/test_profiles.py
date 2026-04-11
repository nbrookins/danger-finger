import inspect

from danger.Params import Params, Prop
from danger.constants import RenderQuality
from danger.finger import DangerFinger
from danger.finger_params import DangerFingerParams
from tests.profiles import COMMON_PLUS_FIT_FIELDS, PROFILES


def _props():
    return {
        name: prop
        for name, prop in inspect.getmembers(DangerFingerParams)
        if isinstance(prop, Prop)
    }


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
