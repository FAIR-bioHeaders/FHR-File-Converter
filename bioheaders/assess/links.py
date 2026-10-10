# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Recorded links to related data, their ranking and conflicts (research R-06).

Every recorded link is reported, strongest first: rank 1 checksum, SeqCol
digest or per-sequence digests; rank 2 accession; rank 3 URL; rank 4 name.
Evidence from upstream GAF blocks is not used. Sequence names and lengths are
never links: they are circumstantial evidence (circumstantial.py).
"""

import re

from .model import Finding, RelatedFileLink
from .synonyms import load as load_synonyms

CONFLICT_KINDS = ("checksum", "seqcol", "accession")


def _comparable(kind, value):
    if kind == "accession" and isinstance(value, str):
        return re.sub(r"^NCBI_Assembly:", "", value)
    return value


def extract(evidence):
    """Return (links, findings, conflicting link evidence ids)."""
    synonyms = load_synonyms()
    links = []
    by_value = {}
    digests = None
    findings = []
    for item_evidence in evidence:
        if item_evidence.scope == "upstream-provenance":
            continue
        for item in item_evidence.items:
            kind = synonyms.link_kind(item.concept)
            if kind is None:
                continue
            relationship = item.extra.get("relationship") or synonyms.relationship(
                item.concept
            )
            well_formed = item.status != "malformed"
            if kind == "sequence-digests":
                if digests is None:
                    digests = RelatedFileLink(
                        "sequence-digests", {}, [item_evidence.id], relationship
                    )
                    links.append(digests)
                elif item_evidence.id not in digests.evidence:
                    digests.evidence.append(item_evidence.id)
                digests.value[item.extra.get("name") or item.value] = item.value
                digests.well_formed = digests.well_formed and well_formed
                continue
            key = (kind, item.value)
            if key in by_value:
                link = by_value[key]
                if item_evidence.id not in link.evidence:
                    link.evidence.append(item_evidence.id)
                continue
            link = RelatedFileLink(
                kind, item.value, [item_evidence.id], relationship, well_formed
            )
            by_value[key] = link
            links.append(link)
            if kind == "url" and synonyms.form_matches("directory-url", item.value):
                findings.append(
                    Finding(
                        "url-names-directory",
                        f"line {item_evidence.line}: the URL {item.value} names a "
                        "directory, not a file, so it does not say which file was used",
                        [item_evidence.id],
                    )
                )
    conflicting = set()
    for kind in CONFLICT_KINDS:
        same = [link for link in links if link.kind == kind and link.well_formed]
        values = {_comparable(kind, link.value) for link in same}
        if len(values) > 1:
            ids = [e for link in same for e in link.evidence]
            conflicting.update(ids)
            findings.append(
                Finding(
                    "conflicting-values",
                    f"the header records {len(values)} different {kind} values for the "
                    f"related data: {', '.join(sorted(map(str, values)))}",
                    ids,
                )
            )
    line_of = {e.id: e.line for e in evidence}
    links.sort(key=lambda link: (link.rank, line_of[link.evidence[0]]))
    return links, findings, conflicting


def is_directory(link):
    return link.kind == "url" and load_synonyms().form_matches(
        "directory-url", link.value
    )
