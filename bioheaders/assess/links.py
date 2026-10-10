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


# Verification against a related file (research R-07) ---------------------------

ACCESSION = re.compile(r"GC[AF]_\d{9}\.\d+")


def _identity(value):
    value = re.sub(r"^https?://identifiers\.org/", "", value.strip())
    value = re.sub(r"^(NCBI_Assembly|insdc\.gca|refseq\.gcf):", "", value, flags=re.I)
    return value


def _hints(link, related_path):
    name = related_path.replace("\\", "/").rsplit("/", 1)[-1]
    value = link.value if isinstance(link.value, str) else ""
    found = ACCESSION.search(value)
    token = found.group(0) if found else value
    if token and token in name:
        return [
            f"the related file's name contains {token}; a file name is not a recorded "
            "identity, so this is not a match"
        ]
    return []


def verify(link, related_file, related_path):
    """Return the LinkVerification of one recorded link."""
    from .model import LinkVerification

    def result(verdict, method, reason=None, expected=None, actual=None, hints=()):
        return LinkVerification(
            related_path,
            verdict,
            method,
            reason,
            link.value if expected is None else expected,
            actual,
            list(hints),
        )

    if not link.well_formed:
        return result("unverifiable", "none", "malformed")
    if related_file.error:
        return result("unverifiable", "none", "related-file-unreadable")
    stated = related_file.stated
    if link.kind == "checksum":
        computed = related_file.computed_checksum
        if computed:
            hints = []
            if stated.get("checksum") and stated["checksum"] != computed:
                hints.append(
                    "the related file's stated checksum does not match its content"
                )
            verdict = "match" if computed == link.value else "mismatch"
            return result(
                verdict, "computed-fhr-checksum", actual=computed, hints=hints
            )
        if stated.get("checksum"):
            verdict = "match" if stated["checksum"] == link.value else "mismatch"
            return result(verdict, "stated-fhr-checksum", actual=stated["checksum"])
        return result("unverifiable", "none", "related-file-states-no-identity")
    if link.kind == "seqcol":
        if stated.get("seqcol_id"):
            verdict = "match" if stated["seqcol_id"] == link.value else "mismatch"
            return result(verdict, "stated-seqcol", actual=stated["seqcol_id"])
        return result("unverifiable", "none", "related-file-states-no-seqcol")
    if link.kind == "sequence-digests":
        names = related_file.names
        absent = sorted(name for name in link.value if name not in names)
        compared = {n: d for n, d in link.value.items() if n in names and names[n][1]}
        if not compared:
            return result("unverifiable", "computed-md5", "sequence-absent")
        differing = sorted(
            n for n, d in compared.items() if d.lower() != names[n][1].lower()
        )
        hints = [f"not in the related file: {', '.join(absent)}"] if absent else []
        if differing:
            return result(
                "mismatch",
                "computed-md5",
                expected={n: link.value[n] for n in differing},
                actual={n: names[n][1] for n in differing},
                hints=hints,
            )
        return result(
            "match",
            "computed-md5",
            actual={n: names[n][1] for n in compared},
            hints=hints,
        )
    values = {
        "accession": stated.get("accessions", []),
        "url": stated.get("urls", []),
        "name": stated.get("names", []),
    }[link.kind]
    hints = _hints(link, related_path)
    if not values:
        return result(
            "unverifiable",
            "stated-identity",
            "related-file-states-no-identity",
            hints=hints,
        )
    wanted = _identity(link.value) if link.kind == "accession" else link.value
    found = [
        v for v in values if (_identity(v) if link.kind == "accession" else v) == wanted
    ]
    if found:
        return result("match", "stated-identity", actual=found[0])
    if link.kind == "accession":
        return result("mismatch", "stated-identity", actual=values[0])
    return result(
        "unverifiable",
        "stated-identity",
        "related-file-states-no-identity",
        actual=values[0],
        hints=hints
        + [f"the related file states {', '.join(values)}, which is not {link.value}"],
    )
