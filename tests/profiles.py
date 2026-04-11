"""Canonical first-wave param profiles for common-plus-fit QA sweeps.

These are intentionally curated, not cartesian. They cover the default adult
index configuration, smaller/larger adults, representative pinky/thumb cases,
one child-sized profile, and one explicit stress profile that pushes the lower
end of the human-range assumptions plus tighter clearances.
"""

from copy import deepcopy


COMMON_PLUS_FIT_FIELDS = (
    "intermediate_length",
    "socket_circumference_proximal",
    "socket_circumference_distal",
    "socket_depth",
    "distal_length",
    "distal_base_length",
    "knuckle_proximal_width",
    "knuckle_distal_width",
    "proximal_length",
    "strut_width",
    "socket_interface_clearance",
    "tip_interface_clearance",
    "knuckle_clearance",
    "knuckle_side_clearance",
)


BASE_COMMON_PLUS_FIT = {
    "intermediate_length": 24.0,
    "socket_circumference_proximal": 63.4,
    "socket_circumference_distal": 57.3,
    "socket_depth": 34.0,
    "distal_length": 24.0,
    "distal_base_length": 6.0,
    "knuckle_proximal_width": 18.5,
    "knuckle_distal_width": 16.0,
    "proximal_length": -0.5,
    "strut_width": 2.0,
    "socket_interface_clearance": 0.03,
    "tip_interface_clearance": 0.3,
    "knuckle_clearance": 0.6,
    "knuckle_side_clearance": 0.12,
}


def _profile(**overrides):
    out = deepcopy(BASE_COMMON_PLUS_FIT)
    out.update(overrides)
    return out


PROFILE_LABELS = {
    "adult_index_default": "Adult index default",
    "adult_index_small": "Adult index small",
    "adult_index_large": "Adult index large",
    "adult_pinky": "Adult pinky",
    "adult_thumb": "Adult thumb",
    "child_index": "Child index",
    "stress_compact": "Stress compact",
}


PROFILES = {
    "adult_index_default": _profile(),
    "adult_index_small": _profile(
        intermediate_length=20.0,
        socket_circumference_proximal=58.0,
        socket_circumference_distal=52.0,
        socket_depth=29.0,
        distal_length=21.0,
        distal_base_length=5.0,
        knuckle_proximal_width=16.0,
        knuckle_distal_width=14.0,
        proximal_length=-0.25,
        strut_width=1.8,
    ),
    "adult_index_large": _profile(
        intermediate_length=27.0,
        socket_circumference_proximal=78.0,
        socket_circumference_distal=71.0,
        socket_depth=40.0,
        distal_length=27.0,
        distal_base_length=7.0,
        knuckle_proximal_width=21.5,
        knuckle_distal_width=18.0,
        proximal_length=1.5,
        strut_width=2.3,
    ),
    "adult_pinky": _profile(
        intermediate_length=21.0,
        socket_circumference_proximal=58.0,
        socket_circumference_distal=54.0,
        socket_depth=30.0,
        distal_length=21.0,
        distal_base_length=5.5,
        knuckle_proximal_width=15.5,
        knuckle_distal_width=13.5,
        proximal_length=0.0,
        strut_width=1.8,
    ),
    "adult_thumb": _profile(
        intermediate_length=22.0,
        socket_circumference_proximal=76.0,
        socket_circumference_distal=70.0,
        socket_depth=32.0,
        distal_length=20.0,
        distal_base_length=7.0,
        knuckle_proximal_width=22.0,
        knuckle_distal_width=19.0,
        proximal_length=1.0,
        strut_width=2.4,
    ),
    "child_index": _profile(
        intermediate_length=18.0,
        socket_circumference_proximal=56.0,
        socket_circumference_distal=52.0,
        socket_depth=29.0,
        distal_length=20.0,
        distal_base_length=5.0,
        knuckle_proximal_width=16.0,
        knuckle_distal_width=14.0,
        proximal_length=0.0,
        strut_width=1.7,
    ),
    "stress_compact": _profile(
        intermediate_length=14.0,
        socket_circumference_proximal=44.0,
        socket_circumference_distal=40.0,
        socket_depth=18.0,
        distal_length=14.0,
        distal_base_length=4.0,
        knuckle_proximal_width=13.0,
        knuckle_distal_width=11.0,
        proximal_length=-0.75,
        strut_width=1.4,
        socket_interface_clearance=-0.05,
        tip_interface_clearance=0.15,
        knuckle_clearance=0.35,
        knuckle_side_clearance=0.05,
    ),
}


PROFILE_ORDER = tuple(PROFILES.keys())
