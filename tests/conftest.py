"""Shared pytest configuration.

Registers Hypothesis profiles and selects one via the ``HYPOTHESIS_PROFILE``
environment variable (defaulting to ``dev``):

- ``dev`` (default): fast feedback for local runs.
- ``ci``: thorough exploration for the test matrix.
"""

import os
from pathlib import Path

from hypothesis import settings

settings.register_profile(
    "dev",
    max_examples=50,
    deadline=None,
)

settings.register_profile(
    "ci",
    max_examples=500,
    deadline=None,
    derandomize=False,
)

settings.load_profile(
    os.environ.get(
        "HYPOTHESIS_PROFILE",
        "dev",
    )
)


def pytest_addoption(parser):
    parser.addoption(
        "--channel-stress",
        choices=("ci", "stress", "soak"),
        default="ci",
        help="Channel stress profile; long profiles are opt-in.",
    )
    parser.addoption(
        "--channel-stress-artifacts",
        type=Path,
        default=Path(".stress-artifacts"),
        help="Directory for channel stress failure traces and campaign summary.",
    )
