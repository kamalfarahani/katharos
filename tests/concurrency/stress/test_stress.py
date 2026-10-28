"""Pytest entry points, bounded-history oracle checks, and harness fault checks."""

import json

import pytest

from .__main__ import campaign, run_case
from .harness import Case
from .models import linearizable


@pytest.mark.channel_stress
def test_channel_campaign(request):
    profile = request.config.getoption("--channel-stress")
    artifacts = request.config.getoption("--channel-stress-artifacts")
    result = campaign(profile, 3500, None, artifacts)
    summary = json.loads((artifacts / "summary.json").read_text())
    assert result == 0, json.dumps(summary["failures"], indent=2)


@pytest.mark.parametrize(
    "fault,scenario",
    [
        ("drop", "delivery"),
        ("duplicate", "delivery"),
        ("missing-notification", "handoff"),
        ("reset-timeout", "timeouts"),
        ("observer-leak", "lifecycle"),
        ("worker-error", "delivery"),
    ],
)
def test_harness_detects_fault(tmp_path, fault, scenario):
    case = Case(scenario, 1, 1, "standard", 1, 1, 4, fault)
    result = run_case(case, tmp_path, watchdog=2)
    assert result["returncode"] != 0 or result["timed_out"], result
    assert (tmp_path / result["trace"]).exists()
    trace = json.loads((tmp_path / result["trace"]).read_text())
    assert trace["case"]["fault"] == fault
    if fault in ("missing-notification", "reset-timeout"):
        assert result["timed_out"]
        assert "Timeout" in result["stderr"] and "Thread" in result["stderr"]
    else:
        assert not result["timed_out"]
        assert "AssertionError" in result["stderr"]
        assert trace["status"] == "failed"
        assert "traceback" in trace
        if fault == "worker-error":
            assert "injected worker error" in trace["worker_errors"][0]


def test_history_checker_accepts_reordering_overlapping_operations():
    history = [
        {"kind": "send", "value": 1, "outcome": ("ok", None), "start": 1, "end": 5},
        {"kind": "recv", "value": None, "outcome": ("ok", 1), "start": 2, "end": 4},
    ]
    assert linearizable(history, 1)


@pytest.mark.parametrize("outcome", [("ok", 2), ("ok", 1)])
def test_history_checker_rejects_impossible_histories(outcome):
    history = [
        {"kind": "send", "value": 1, "outcome": ("ok", None), "start": 1, "end": 2},
        {"kind": "recv", "value": None, "outcome": ("ok", 1), "start": 3, "end": 4},
        {"kind": "recv", "value": None, "outcome": outcome, "start": 5, "end": 6},
    ]
    assert not linearizable(history, 1)
