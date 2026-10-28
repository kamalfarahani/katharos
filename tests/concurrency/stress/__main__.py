"""Run bounded channel stress campaigns, isolating each case in a subprocess."""

from __future__ import annotations

import argparse
import faulthandler
import json
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

from .harness import Case, Context
from .models import histories, sequential
from .scenarios import SCENARIOS, missing_notification, observer_fault

SCENARIOS.update({"model": sequential, "history": histories})
PROFILES = {
    "ci": {"seconds": 0, "watchdog": 15, "max_workers": 8, "messages": 24},
    "stress": {"seconds": 900, "watchdog": 30, "max_workers": 32, "messages": 100},
    "soak": {"seconds": 7200, "watchdog": 60, "max_workers": 32, "messages": 250},
}


def run_case(case, artifacts_dir, watchdog):
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{case.scenario}-{case.seed}-{case.backend}-{time.time_ns()}"
    trace = artifacts_dir / f"{stem}.json"
    command = [
        sys.executable,
        "-m",
        "tests.concurrency.stress",
        "--child",
        json.dumps(asdict(case)),
        "--trace-file",
        str(trace),
        "--watchdog",
        str(watchdog),
    ]
    started = time.monotonic()
    with (
        (artifacts_dir / f"{stem}.stdout").open("w+") as stdout,
        (artifacts_dir / f"{stem}.stderr").open("w+") as stderr,
    ):
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        timed_out = False
        try:
            process.wait(timeout=watchdog)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        except BaseException:
            process.kill()
            process.wait(timeout=2)
            raise
        stdout.seek(0)
        stderr.seek(0)
        output, errors = stdout.read(), stderr.read()
    result = {
        "case": asdict(case),
        "returncode": process.returncode,
        "timed_out": timed_out,
        "elapsed": time.monotonic() - started,
        "watchdog": watchdog,
        "trace": str(trace),
        "stdout": output,
        "stderr": errors,
    }
    if process.returncode == 0 and not timed_out:
        trace.unlink(missing_ok=True)
        trace.with_suffix(".stdout").unlink(missing_ok=True)
        trace.with_suffix(".stderr").unlink(missing_ok=True)
    else:
        (artifacts_dir / f"{stem}.failure.json").write_text(
            json.dumps(result, indent=2)
        )
    return result


def child(case, trace, watchdog):
    faulthandler.enable()
    faulthandler.dump_traceback_later(max(0.1, watchdog * 0.8), repeat=False)
    ctx = Context(case, trace)
    ctx.flush(watchdog=watchdog)
    try:
        if case.fault == "missing-notification":
            missing_notification(ctx)
        elif case.fault == "observer-leak":
            observer_fault(ctx)
        elif case.fault == "worker-error":

            def broken_worker():
                raise RuntimeError("injected worker error")

            ctx.spawn("broken-worker", broken_worker)
        else:
            SCENARIOS[case.scenario](ctx)
        ctx.finish()
    except BaseException:  # noqa: BLE001 - child failures must become trace artifacts
        traceback.print_exc()
        ctx.flush(status="failed", traceback=traceback.format_exc())
        try:
            ctx.finish()
        except BaseException:  # noqa: BLE001 - retain the primary failure on cleanup errors
            traceback.print_exc()
        return 1
    finally:
        faulthandler.cancel_dump_traceback_later()
    return 0


def campaign(profile, seed, scenario, artifacts_dir):
    settings = PROFILES[profile]
    families = [scenario] if scenario else list(SCENARIOS)
    started = time.monotonic()
    count = 0
    failures = []
    # Each round covers every scenario, backend, capacity and CI topology.
    backends = ("standard", "lock", "perturbed")
    capacities = (0, 1, 2, 16) if profile == "ci" else (0, 1, 2, 16, 256)
    topologies = ((1, 1), (8, 1), (1, 8), (8, 8))
    round_index = 0
    while True:
        for index in range(max(len(capacities), len(topologies))):
            for backend_index, backend in enumerate(backends):
                for family in families:
                    topology = (index + backend_index) % len(topologies)
                    if index == 0 and backend_index == 2:
                        topology = 3  # Contended unbuffered hand-offs in the CI tier.
                    producers, consumers = topologies[topology]
                    if profile != "ci" and round_index % 2:
                        producers = consumers = settings["max_workers"]
                    case = Case(
                        family,
                        seed + round_index * 1009 + index,
                        capacities[index % len(capacities)],
                        backend,
                        producers,
                        consumers,
                        settings["messages"],
                    )
                    result = run_case(case, artifacts_dir, settings["watchdog"])
                    count += 1
                    if result["returncode"] or result["timed_out"]:
                        failures.append(result)
                        print(
                            f"FAIL {family} seed={case.seed} backend={backend}: "
                            f"{result['trace']}",
                            flush=True,
                        )
                    else:
                        print(
                            f"PASS {family} seed={case.seed} backend={backend}",
                            flush=True,
                        )
                    summary = {
                        "profile": profile,
                        "seed": seed,
                        "cases": count,
                        "elapsed": time.monotonic() - started,
                        "failures": failures,
                    }
                    Path(artifacts_dir, "summary.json").write_text(
                        json.dumps(summary, indent=2)
                    )
                    if failures:
                        return 1
                    # Always complete the first round, then honor the time budget.
                    if (
                        round_index
                        and time.monotonic() - started >= settings["seconds"]
                    ):
                        return 0
        round_index += 1
        if time.monotonic() - started >= settings["seconds"]:
            return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, default="ci")
    parser.add_argument("--seed", type=int, default=3500)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--artifacts-dir", type=Path, default=Path(".stress-artifacts"))
    parser.add_argument("--replay", type=Path, help="Replay a saved case trace JSON")
    parser.add_argument("--child", help=argparse.SUPPRESS)
    parser.add_argument("--trace-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--watchdog", type=float, default=15, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        return child(Case(**json.loads(args.child)), args.trace_file, args.watchdog)
    if args.replay:
        saved = json.loads(args.replay.read_text())
        case = Case(**saved["case"])
        result = run_case(
            case,
            args.artifacts_dir,
            saved.get("watchdog", PROFILES[args.profile]["watchdog"]),
        )
        print(json.dumps(result, indent=2))
        return int(bool(result["returncode"] or result["timed_out"]))
    return campaign(args.profile, args.seed, args.scenario, args.artifacts_dir)


if __name__ == "__main__":
    raise SystemExit(main())
