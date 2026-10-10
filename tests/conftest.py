# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Test configuration: the assessment tests run with network access disabled."""

import socket

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "online_local: assessment test allowed to use local sockets"
    )


@pytest.fixture(autouse=True)
def _no_network_in_assessment_tests(request, monkeypatch):
    """Make ``socket.connect`` raise in ``assess_*_test.py`` modules (FR-010)."""
    name = request.node.fspath.basename
    if not (name.startswith("assess_") and name.endswith("_test.py")):
        yield
        return
    if request.node.get_closest_marker("online_local"):
        yield
        return

    def refuse(self, *args, **kwargs):
        raise OSError("network access is disabled in assessment tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    yield
