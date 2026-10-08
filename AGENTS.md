# Agent instructions

## Strategy and boundaries

Read README, relevant issue requirements, and current code before editing. The
[2024 FHR paper](https://doi.org/10.1093/bib/bbae122) motivates minimal metadata,
multiple serializations, provenance tied closely to data, compatibility, FAIR,
and TRUST. Practical interpretation: preserve user metadata and sequence bytes,
keep required fields/dependencies small, and prefer interoperable incremental
changes over speculative frameworks. These are implementation guidelines inferred
from the paper, not quotations or governance rules.

David and Adam are the maintainers and jointly hold schema and release authority
(GOVERNANCE.md). The documented steering-group option is not active; do not treat
it as current authority.

## Repository map

`fhr/__init__.py` holds the mapping, input/output methods, and packaged schema loading. `fhr/cli.py` implements all installed commands; old top-level and FASTA/GFA files are compatibility wrappers. `fhr/fhr_schema.json` is included in distributions; root `fhr_schema.json` is a compatibility copy. `tests/fhr_test.py` covers semantic round trips, validation, and exact-byte sequence helpers. Poetry config defines eight entry points.

## Verification

Run relevant checks from the repository root:

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run isort . --check-only
poetry run black . --check
```

For schema changes, inspect compatibility of valid existing instances, required
fields, types, unknown-property policy, patterns, URI/date formats, and optional
values. Synchronize the published schema and both converter copies. Review the
schema diff before intentionally updating `.github/schema-baseline.json`; never
refresh it simply to hide a failed check. For serialization changes, test all
formats and HTML escaping/typed values. For sequence tools, test metadata and
sequence tampering, CRLF, ordinary comments, combine/strip, and installed commands
from outside the checkout. Record environment limitations and failed checks.

Use exact file bytes for SHA-512/256 coverage except the scalar checksum line;
read the format policy before editing checksum behavior. SeqCol is a supplied
collection identifier, not an FHR checksum. Use authoritative pinned MIxS terms
and report partial/lossy mappings explicitly; do not invent accessions or metadata.

Update examples, README, citations, and release notes alongside behavior changes.
Keep cross-repo PR links current. Publishing, adoption of governance, and reporting
contact confirmation are separate maintainer actions. Do not fabricate contacts
or claim a policy has been adopted.
