import importlib
import subprocess
import sys
from textwrap import dedent

import pytest

from katharos.concurrency.csp import CSPRuntime, default_csp_runtime
from katharos.concurrency.threading_backend import ThreadingBackend, default_backend


def test_default_runtime_export_is_shared():
    package = importlib.import_module("katharos.concurrency.csp")
    implementation = importlib.import_module("katharos.concurrency.csp.runtime")

    assert isinstance(default_csp_runtime, CSPRuntime)
    assert package.default_csp_runtime is default_csp_runtime
    assert implementation.default_csp_runtime is default_csp_runtime


@pytest.mark.parametrize("custom_backend", [False, True], ids=["default", "custom"])
def test_runtime_binds_backend_and_completes_channel_scope(custom_backend):
    backend = ThreadingBackend() if custom_backend else default_backend()
    runtime = CSPRuntime(backend) if custom_backend else default_csp_runtime
    channel = runtime.Channel[int]()
    sent = []

    assert runtime.backend is backend
    assert channel.backend is backend
    assert runtime.go._backend is backend

    def send_value():
        sent.append(channel.send(42))

    with runtime.go:
        handle = runtime.go(send_value)
        try:
            received = channel.recv(timeout=1)
        finally:
            channel.close()

    assert received.unwrap() == 42
    assert [result.unwrap() for result in sent] == [None]
    assert not handle.is_alive()


def test_removed_runtime_names_are_unavailable_in_fresh_interpreter():
    script = dedent(
        """
        import importlib

        package = importlib.import_module("katharos.concurrency.csp")
        implementation = importlib.import_module("katharos.concurrency.csp.runtime")
        assert package.default_csp_runtime is implementation.default_csp_runtime
        assert "default_csp_runtime" in package.__all__
        assert "csp" not in package.__all__
        assert not hasattr(package, "csp")

        try:
            from katharos.concurrency.csp import csp
        except ImportError:
            pass
        else:
            raise AssertionError("The removed public csp name is still importable")

        try:
            importlib.import_module("katharos.concurrency.csp.csp")
        except ModuleNotFoundError as error:
            assert error.name == "katharos.concurrency.csp.csp"
        else:
            raise AssertionError("The old runtime module is still importable")
        """
    )

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
