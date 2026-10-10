# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Report output: schema validity, reproducibility, wording, escaping (T023)."""

import re
import socket

import pytest
from assess_helpers import ALL_HEADER_FIXTURES, FIXTURES, assess

from bioheaders.assess import render

FORBIDDEN = re.compile(r"score|is FAIR|certified", re.IGNORECASE)


def _without_cited_lines(text, report):
    """Our own wording: remove the provider lines quoted as evidence."""
    for item in sorted(report["evidence"], key=lambda i: -len(i["raw"])):
        for form in (item["raw"], render.escape_markdown(item["raw"])):
            text = text.replace(render.shorten(form), "")
    return text


@pytest.mark.parametrize("name", ALL_HEADER_FIXTURES)
def test_reports_validate_and_are_reproducible(name):
    first, second = assess(name), assess(name)
    assert render.to_json(first) == render.to_json(second)
    assert render.to_markdown(first) == render.to_markdown(second)
    assert render.to_text(first) == render.to_text(second)
    text = render.to_json(first)
    assert text.endswith("}\n") and "\r" not in text


@pytest.mark.parametrize("name", ALL_HEADER_FIXTURES)
def test_no_score_wording(name):
    report = assess(name)
    for text in (render.to_text(report), render.to_markdown(report)):
        assert not FORBIDDEN.search(_without_cited_lines(text, report))


@pytest.mark.parametrize("name", ["no-header.fa", "go_gaf_wb.gaf"])
def test_attribution_and_online_line_everywhere(name):
    report = assess(name)
    assert "10.15497/rda00050" in report["attribution"]
    assert report["online_checks"] == "not_requested"
    assert "online" not in report
    for text in (render.to_text(report), render.to_markdown(report)):
        assert "10.15497/rda00050" in text
        assert "Online checks: not requested" in text


def test_no_socket_is_opened(monkeypatch):
    opened = []
    original = socket.socket.__init__

    def record(self, *args, **kwargs):
        opened.append(args)
        original(self, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "__init__", record)
    assess("ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff")
    assert opened == []


def test_markdown_escapes_cited_lines(tmp_path):
    path = tmp_path / "e.gff3"
    path.write_bytes(b"##gff-version 3\n#!data-source A|B <i>`x`</i>\n")
    report = assess(path)
    markdown = render.to_markdown(report)
    assert "A\\|B &lt;i&gt;\\`x\\`&lt;/i&gt;" in markdown
    assert "<i>" not in markdown


def test_to_json_rejects_a_nonconforming_report():
    report = assess("no-header.fa")
    report["score"] = 1
    with pytest.raises(ValueError, match="does not conform"):
        render.to_json(report)


def test_sections_in_order():
    text = render.to_text(assess(FIXTURES / "fhr-valid.fhr.fasta"))
    order = [
        "FAIR header assessment:",
        "Online checks:",
        "FAIR-bioHeaders conformance",
        "Findable",
        "Accessible",
        "Interoperable",
        "Reusable",
        "Recorded links",
        "Findings",
        "Indicator identifiers and titles from",
    ]
    positions = [text.index(heading) for heading in order]
    assert positions == sorted(positions)
