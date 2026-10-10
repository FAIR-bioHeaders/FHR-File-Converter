# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Shared helpers for the assessment tests."""

from pathlib import Path

from bioheaders.assess import assess_file

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "assess"
REFSEQ_GFF3 = "ncbi-refseq_gff3_GCF_000002985.6_WBcel235_genomic.gff"
ALL_HEADER_FIXTURES = sorted(
    path.name
    for path in FIXTURES.iterdir()
    if path.is_file() and path.name != "README.md"
)


def assess(name, **options):
    path = name if isinstance(name, Path) else FIXTURES / name
    return assess_file(path, **options)


def result(report, indicator):
    (found,) = [r for r in report["results"] if r["indicator"] == indicator]
    return found


def status(report, indicator):
    return result(report, indicator)["status"]


def evidence_by_id(report):
    return {item["id"]: item for item in report["evidence"]}


def cited_lines(report, indicator):
    items = evidence_by_id(report)
    return sorted(items[e]["line"] for e in result(report, indicator)["evidence"])


def all_findings(report):
    findings = list(report["findings"])
    for item in report["results"]:
        findings += item["findings"]
    return findings


def finding_lines(report, kind):
    items = evidence_by_id(report)
    return sorted(
        {
            items[e]["line"]
            for finding in all_findings(report)
            if finding["kind"] == kind
            for e in finding["evidence"]
        }
    )
