# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Name and length consistency with a related file (FR-005, research R-08).

This is circumstantial evidence, not a recorded link: it is reported in its own
section and never credited under any indicator.
"""

from .model import CircumstantialCheck


def declared_sequences(evidence, seqids):
    """Return (source, {name: declared length or None}) from the derived file."""
    regions, contigs = {}, {}
    for item in evidence:
        if item.scope != "file" or not isinstance(item.value, dict):
            continue
        if item.convention == "gff3-directive" and item.key == "sequence-region":
            value = item.value
            length = value["end"] if value.get("start") == 1 else None
            regions.setdefault(value["seqid"], length)
        elif (
            item.convention == "vcf-meta"
            and item.key == "contig"
            and "ID" in item.value
        ):
            length = item.value.get("length")
            contigs.setdefault(
                item.value["ID"], int(length) if length and length.isdigit() else None
            )
    if regions:
        return "sequence-region", regions
    if contigs:
        return "vcf-contig", contigs
    if seqids:
        return "record-seqids", {name: None for name in seqids}
    return "none", {}


def check(evidence, seqids, related_file, related_path):
    source, declared = declared_sequences(evidence, seqids)
    result = CircumstantialCheck(related_path=related_path, source=source)
    if related_file.error or not declared:
        return result
    names = related_file.names
    result.names_compared = len(declared)
    result.missing_from_related = sorted(name for name in declared if name not in names)
    for name, length in declared.items():
        if name in names and length is not None:
            result.lengths_compared += 1
            actual = names[name][0]
            if actual != length:
                result.length_mismatches.append(
                    {"name": name, "declared": length, "actual": actual}
                )
    result.not_declared_count = len(set(names) - set(declared))
    if len(result.missing_from_related) == len(declared):
        result.verdict = "inconsistent"
    elif not result.missing_from_related and not result.length_mismatches:
        result.verdict = "consistent"
    else:
        result.verdict = "partially_consistent"
    return result


def classify(verdicts, circumstantial_verdict):
    """Pair classification, data-model §10 (first rule that holds wins)."""
    if "mismatch" in verdicts:
        return "recorded-mismatch"
    if "match" in verdicts:
        return "recorded-match"
    return {
        "inconsistent": "inconsistent",
        "partially_consistent": "partial",
        "consistent": "consistent-unverified",
    }.get(circumstantial_verdict, "unknown")
