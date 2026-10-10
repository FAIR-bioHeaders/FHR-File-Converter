# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Report entities of the FAIR header assessment (specs/010 data-model.md).

Each class has ``to_json()`` returning the JSON form defined by
``assessment-report.schema.json``. The status rules of data-model §5 that can
be checked on one object are enforced in ``__post_init__``.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

STATUSES = (
    "evidenced",
    "partially_evidenced",
    "not_evidenced",
    "not_applicable",
    "not_assessed",
)
NOT_APPLICABLE_REASONS = ("embedded-metadata", "repository-level", "object-in-hand")
NOT_ASSESSED_REASONS = (
    "online-check-not-requested",
    "online-check-unavailable",
    "deferred-data-body",
    "binary-format-out-of-scope",
    "archive-not-supported",
    "unsupported-header-type",
    "unsupported-schema-version",
    "input-unreadable",
)
LINK_RANKS = {
    "checksum": 1,
    "seqcol": 1,
    "sequence-digests": 1,
    "accession": 2,
    "url": 3,
    "name": 4,
}


def _json(value):
    if hasattr(value, "to_json"):
        return value.to_json()
    if isinstance(value, list):
        return [_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    return value


@dataclass
class InputFile:
    path: str
    size: Optional[int]
    compression: str
    format: str
    format_source: str
    scope: str
    header_lines_read: int = 0
    records_sampled: int = 0
    header_sha256: Optional[str] = None
    file_sha256: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.scope == "error" and not self.error:
            raise ValueError("an input with scope error needs an error message")
        if self.scope == "assessed" and not self.header_sha256:
            raise ValueError("an assessed input needs header_sha256")

    def to_json(self):
        result = {
            "path": self.path,
            "size": self.size,
            "compression": self.compression,
            "format": self.format,
            "format_source": self.format_source,
            "scope": self.scope,
            "header_lines_read": self.header_lines_read,
            "records_sampled": self.records_sampled,
        }
        for name in ("header_sha256", "file_sha256", "error"):
            if getattr(self, name) is not None:
                result[name] = getattr(self, name)
        return result


@dataclass
class HeaderEvidence:
    id: str
    line: int
    convention: str
    raw: str
    key: Optional[str] = None
    normalised_key: Optional[str] = None
    value: Any = None
    concepts: List[str] = field(default_factory=list)
    scope: str = "file"
    value_forms: List[str] = field(default_factory=list)

    def to_json(self):
        return {
            "id": self.id,
            "line": self.line,
            "convention": self.convention,
            "raw": self.raw,
            "key": self.key,
            "normalised_key": self.normalised_key,
            "value": self.value,
            "concepts": list(self.concepts),
            "scope": self.scope,
            "value_forms": list(self.value_forms),
        }


@dataclass
class Finding:
    kind: str
    message: str
    evidence: List[str] = field(default_factory=list)

    def to_json(self):
        return {
            "kind": self.kind,
            "evidence": list(self.evidence),
            "message": self.message,
        }


@dataclass
class Suggestion:
    text: str
    line: str
    convention: str
    value_source: str
    guideline_item: str

    def __post_init__(self):
        if self.value_source not in (
            "file",
            "related-file",
            "placeholder",
            "file-name",
        ):
            raise ValueError(f"unknown value source {self.value_source}")
        if self.value_source == "file-name" and "confirm before use" not in self.text:
            raise ValueError("a value from the file name must say 'confirm before use'")

    def to_json(self):
        return {
            "text": self.text,
            "line": self.line,
            "convention": self.convention,
            "value_source": self.value_source,
            "guideline_item": self.guideline_item,
        }


@dataclass
class IndicatorResult:
    indicator: str
    status: str
    reason: Optional[str] = None
    method: str = "offline"
    evidence: List[str] = field(default_factory=list)
    conditions_met: int = 0
    conditions_total: int = 0
    findings: List[Finding] = field(default_factory=list)
    suggestion: Optional[Suggestion] = None
    notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status}")
        needs_reason = self.status in ("not_applicable", "not_assessed")
        if needs_reason != (self.reason is not None):
            raise ValueError(
                f"{self.indicator}: reason required iff not_applicable or not_assessed"
            )
        allowed = {
            "not_applicable": NOT_APPLICABLE_REASONS,
            "not_assessed": NOT_ASSESSED_REASONS,
        }.get(self.status)
        if allowed and self.reason not in allowed:
            raise ValueError(f"{self.indicator}: reason {self.reason} not allowed")
        needs_suggestion = self.status in ("partially_evidenced", "not_evidenced")
        if needs_suggestion != (self.suggestion is not None):
            raise ValueError(
                f"{self.indicator}: suggestion required iff partially or not evidenced"
            )
        if self.status in ("evidenced", "partially_evidenced") and not self.evidence:
            raise ValueError(f"{self.indicator}: evidenced statuses need evidence")
        if self.status == "not_applicable" or (
            self.status == "not_assessed" and self.method != "online"
        ):
            self.method = "none"

    def to_json(self):
        result = {
            "indicator": self.indicator,
            "status": self.status,
            "reason": self.reason,
            "method": self.method,
            "evidence": list(self.evidence),
            "conditions_met": self.conditions_met,
            "conditions_total": self.conditions_total,
            "findings": _json(self.findings),
            "suggestion": _json(self.suggestion),
        }
        if self.notes:
            result["notes"] = list(self.notes)
        return result


@dataclass
class LinkVerification:
    related_path: str
    verdict: str
    method: str
    reason: Optional[str] = None
    expected: Any = None
    actual: Any = None
    hints: List[str] = field(default_factory=list)

    def __post_init__(self):
        if (self.verdict == "unverifiable") != (self.reason is not None):
            raise ValueError("reason required iff the verdict is unverifiable")

    def to_json(self):
        return {
            "related_path": self.related_path,
            "verdict": self.verdict,
            "reason": self.reason,
            "expected": self.expected,
            "actual": self.actual,
            "method": self.method,
            "hints": list(self.hints),
        }


@dataclass
class RelatedFileLink:
    kind: str
    value: Any
    evidence: List[str]
    relationship: Optional[str] = None
    well_formed: bool = True
    verification: Optional[LinkVerification] = None

    def __post_init__(self):
        if not self.evidence:
            raise ValueError("a recorded link needs evidence")

    @property
    def rank(self):
        return LINK_RANKS[self.kind]

    def to_json(self):
        return {
            "kind": self.kind,
            "rank": self.rank,
            "value": self.value,
            "relationship": self.relationship,
            "evidence": list(self.evidence),
            "well_formed": self.well_formed,
            "verification": _json(self.verification),
        }


@dataclass
class CircumstantialCheck:
    related_path: str
    source: str
    names_compared: int = 0
    lengths_compared: int = 0
    missing_from_related: List[str] = field(default_factory=list)
    length_mismatches: List[Dict[str, Any]] = field(default_factory=list)
    not_declared_count: int = 0
    verdict: str = "not_checked"
    label: str = "circumstantial evidence, not a recorded link"

    def to_json(self):
        return {
            "label": self.label,
            "related_path": self.related_path,
            "source": self.source,
            "names_compared": self.names_compared,
            "lengths_compared": self.lengths_compared,
            "missing_from_related": sorted(self.missing_from_related),
            "length_mismatches": [dict(item) for item in self.length_mismatches],
            "not_declared_count": self.not_declared_count,
            "verdict": self.verdict,
        }


@dataclass
class ConformanceResult:
    header_type: Optional[str]
    cited_schema: Optional[str]
    cited_schema_version: Optional[str]
    schema_used: Optional[Dict[str, str]]
    result: str
    reason: Optional[str] = None

    def __post_init__(self):
        if (self.result == "valid") != (self.reason is None):
            raise ValueError("reason required unless the result is valid")

    def to_json(self):
        return {
            "header_type": self.header_type,
            "cited_schema": self.cited_schema,
            "cited_schema_version": self.cited_schema_version,
            "schema_used": self.schema_used,
            "result": self.result,
            "reason": self.reason,
        }


@dataclass
class OnlineCheck:
    target: str
    request_url: str
    outcome: str
    checked_at: str
    final_url: Optional[str] = None
    http_status: Optional[int] = None

    def to_json(self):
        return {
            "target": self.target,
            "request_url": self.request_url,
            "final_url": self.final_url,
            "http_status": self.http_status,
            "outcome": self.outcome,
            "checked_at": self.checked_at,
            "time_dependent": True,
        }


@dataclass
class AssessmentReport:
    tool_version: str
    rubric_version: str
    synonyms_version: str
    reference_versions: Dict[str, str]
    attribution: str
    input: InputFile
    evidence: List[HeaderEvidence] = field(default_factory=list)
    results: List[IndicatorResult] = field(default_factory=list)
    conformance: Optional[ConformanceResult] = None
    links: List[RelatedFileLink] = field(default_factory=list)
    circumstantial: Optional[CircumstantialCheck] = None
    pair_classification: Optional[str] = None
    findings: List[Finding] = field(default_factory=list)
    online: Optional[List[OnlineCheck]] = None
    report_version: str = "1.0.0"

    def to_json(self):
        result = {
            "report_version": self.report_version,
            "tool": {"name": "bioheaders assess", "version": self.tool_version},
            "rubric_version": self.rubric_version,
            "synonyms_version": self.synonyms_version,
            "reference_versions": dict(self.reference_versions),
            "attribution": self.attribution,
            "online_checks": "not_requested" if self.online is None else "ran",
            "input": self.input.to_json(),
            "evidence": _json(self.evidence),
            "results": _json(self.results),
            "conformance": _json(self.conformance),
            "links": _json(self.links),
            "circumstantial": _json(self.circumstantial),
            "pair_classification": self.pair_classification,
            "findings": _json(self.findings),
        }
        if self.online is not None:
            result["online"] = {"checks": _json(self.online)}
        return result
