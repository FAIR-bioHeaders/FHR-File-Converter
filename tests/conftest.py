# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Test configuration: the assessment and JSON-LD tests run with network access disabled."""

import socket

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "online_local: assessment test allowed to use local sockets"
    )


@pytest.fixture(autouse=True)
def _no_network_in_assessment_tests(request, monkeypatch):
    """Make ``socket.connect`` raise in ``assess_*_test.py`` modules (010 FR-010)
    and in ``jsonld_test.py`` (011 FR-005: JSON-LD works offline)."""
    name = request.node.fspath.basename
    offline = name == "jsonld_test.py" or (
        name.startswith("assess_") and name.endswith("_test.py")
    )
    if not offline:
        yield
        return
    if request.node.get_closest_marker("online_local"):
        yield
        return

    def refuse(self, *args, **kwargs):
        raise OSError(f"network access is disabled in {name}")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    yield
