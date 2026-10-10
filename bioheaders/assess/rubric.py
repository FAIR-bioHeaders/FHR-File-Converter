# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Derive each indicator's status (data-model §5, steps 1-9).

1. not_applicable indicators keep their rubric reason.
2. Inputs that are out of scope or unreadable: not_assessed with that reason.
3. Deferred (data-body) indicators: not_assessed (deferred-data-body).
4. Online indicators without --online: not_assessed (online-check-not-requested).
5. Online network failures: not_assessed (online-check-unavailable).
6. The fhr-conformance check when conformance was not assessed: its reason.
7. Conditions over credited evidence (no upstream provenance, nothing malformed,
   nothing from an invalid FAIR-bioHeaders header), then the rubric's rules.
8. Caps, only downwards: evidence that is all first-record, or a conflicting
   value, gives at most partially_evidenced; a truncated header is reported.
9. Online results never lower a status reached in step 7 or 8.
"""

from .links import is_directory
from .synonyms import load as load_synonyms

SCOPE_REASONS = {
    "binary": "binary-format-out-of-scope",
    "archive": "archive-not-supported",
}
STATUS_ORDER = ("not_evidenced", "partially_evidenced", "evidenced")


class Context:
    """Everything the status rules read."""

    def __init__(self, **values):
        self.scope = values.get("scope", "assessed")
        self.format = values.get("format")
        self.evidence = values.get("evidence", [])
        self.findings = values.get("findings", [])
        self.conformance = values.get("conformance")
        self.links = values.get("links", [])
        self.conflicting = values.get("conflicting", set())
        self.records = values.get("records", 0)
        self.records_ok = values.get("records_ok", False)
        self.truncated = values.get("truncated", False)
        self.formats = values.get("formats", {})
        self.online = values.get("online", False)


def _rule(rule, satisfied, ids):
    if rule == "all":
        return len(satisfied) == len(ids)
    if rule == "any":
        return bool(satisfied)
    if rule == "never":
        return False
    if "min" in rule:
        return len(satisfied) >= rule["min"]
    if "any_of" in rule:
        return any(name in satisfied for name in rule["any_of"])
    return all(name in satisfied for name in rule["all_of"])


def _credited(context):
    for evidence in context.evidence:
        if evidence.scope == "upstream-provenance":
            continue
        for item in evidence.items:
            if item.status != "malformed":
                yield evidence, item


def _generic(condition, context, synonyms):
    """Evidence (id, scope) pairs that satisfy ``condition``."""
    allowed = condition.get("scope_allowed", ["file"])
    form = condition.get("form")
    found = []
    for evidence, item in _credited(context):
        if item.concept != condition["concept"] or evidence.scope not in allowed:
            continue
        if (
            form
            and form not in item.forms
            and not synonyms.form_matches(form, item.value)
        ):
            continue
        found.append((evidence.id, evidence.scope))
    return found


def _named(indicator, condition, context, synonyms):
    """Named checks (rubric ``check``); None means: evaluate generically."""
    check = indicator.get("check")
    name = condition["id"]
    scope_of = {e.id: e.scope for e in context.evidence}

    def pairs(ids):
        return [(i, scope_of[i]) for i in ids]

    if check == "derived-link":
        if name == "identifier-reference":
            chosen = [
                link
                for link in context.links
                if link.well_formed and link.rank <= 3 and not is_directory(link)
            ]
        elif name == "relationship-stated":
            chosen = [link for link in context.links if link.relationship]
        elif name == "name-reference":
            chosen = list(context.links)
        else:
            return None
        return pairs([e for link in chosen for e in link.evidence])
    if check in ("format-declared", "record-sample-parse", "fhr-conformance"):
        declared = _generic({"concept": "format-version"}, context, synonyms)
        schema = (
            _generic({"concept": "header-schema"}, context, synonyms)
            if context.conformance is not None
            and context.conformance.result != "invalid"
            else []
        )
        fhr_valid = (
            context.conformance is not None and context.conformance.result == "valid"
        )
        if name == "format-declared":
            return declared + schema
        if name == "listed-format-declared":
            table = context.formats.get(context.format)
            if table is None:
                return []
            listed = [(i, s) for i, s in declared if _listed_version(i, context, table)]
            return listed + schema
        if name == "records-parse":
            if context.records and context.records_ok and (declared or schema):
                return declared + schema
            return []
        if name == "convention-met":
            if fhr_valid:
                return schema
            if (
                context.conformance is not None
                and context.conformance.result == "invalid"
            ):
                return []
            first = next((e for e in context.evidence), None)
            return [(i, s) for i, s in declared if first is not None and i == first.id]
        if name == "schema-valid":
            return schema if fhr_valid else []
    return None


def _listed_version(evidence_id, context, table):
    evidence = next(e for e in context.evidence if e.id == evidence_id)
    value = evidence.value if isinstance(evidence.value, str) else ""
    value = value.strip()
    directive = table.get("version_directive") or ""
    if directive.startswith("##fileformat=VCFv"):
        value = value[len("VCFv") :] if value.startswith("VCFv") else ""
    return value in table.get("versions", [])


def _result(indicator, status, reason=None, **values):
    return dict(indicator=indicator, status=status, reason=reason, **values)


def evaluate(indicator, context):
    """Return the IndicatorResult fields of one rubric indicator (no suggestion)."""
    synonyms = load_synonyms()
    identifier = indicator["id"]
    assessability = indicator["assessability"]
    if assessability == "not_applicable":
        return _result(identifier, "not_applicable", indicator["reason"])
    if context.scope != "assessed":
        reason = SCOPE_REASONS.get(context.format, "input-unreadable")
        if context.scope == "error":
            reason = "input-unreadable"
        return _result(identifier, "not_assessed", reason)
    if assessability == "deferred":
        return _result(identifier, "not_assessed", indicator["reason"])
    if assessability == "online" and not context.online:
        return _result(identifier, "not_assessed", "online-check-not-requested")
    if (
        indicator.get("check") == "fhr-conformance"
        and context.conformance is not None
        and context.conformance.result == "not_assessed"
    ):
        return _result(identifier, "not_assessed", context.conformance.reason)
    conditions = indicator["conditions"]
    satisfied = {}
    for condition in conditions:
        found = _named(indicator, condition, context, synonyms)
        if found is None:
            found = _generic(condition, context, synonyms)
        if found:
            satisfied[condition["id"]] = found
    ids = [condition["id"] for condition in conditions]
    if _rule(indicator["evidenced_when"], satisfied, ids):
        status = "evidenced"
    elif _rule(indicator["partial_when"], satisfied, ids):
        status = "partially_evidenced"
    else:
        status = "not_evidenced"
    used = sorted(
        {e for found in satisfied.values() for e, _ in found},
        key=lambda e: int(e[1:]),
    )
    scopes = {s for found in satisfied.values() for _, s in found}
    relevant = _relevant_evidence(indicator, context)
    findings = [
        finding
        for finding in context.findings
        if set(finding.evidence) & relevant
        or (
            not finding.evidence
            and finding.kind == "header-truncated"
            and status != "evidenced"
        )
    ]
    if status == "evidenced" and scopes == {"first-record"}:
        status = "partially_evidenced"
    if status == "evidenced" and set(used) & context.conflicting:
        status = "partially_evidenced"
    return _result(
        identifier,
        status,
        method="offline",
        evidence=used if status != "not_evidenced" else [],
        conditions_met=len(satisfied),
        conditions_total=len(conditions),
        findings=findings,
        satisfied=set(satisfied),
    )


def _relevant_evidence(indicator, context):
    concepts = {c["concept"] for c in indicator.get("conditions", [])}
    relevant = {
        e.id for e in context.evidence if any(i.concept in concepts for i in e.items)
    }
    if indicator.get("check") == "derived-link":
        relevant.update(e for link in context.links for e in link.evidence)
    return relevant
