# Contributing

Start with an issue describing the use case or failure and a small reproducible
example. Submit a focused branch/PR with behavior, compatibility implications,
and relevant validation. Link related work in [FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification)
and the release tracker when a change spans repositories. Do not include private
genome data, credentials, or unrelated formatting in fixtures.

## Setup and checks

See README for Python requirements and environment setup. From this checkout:

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run isort . --check-only
poetry run black . --check
```

Changes to metadata must coordinate `fhr.json`, the LinkML model, both converter
schema copies, serializers, examples, and documentation. Add regression tests
for changed behavior, including minimal metadata and relevant invalid cases.
Document checksum semantics and migration rather than silently changing identity.
Keep required metadata and runtime dependencies small.

David and Adam retain schema authority. The [successor governance proposal](https://github.com/FAIR-bioHeaders/FHR-Specification/blob/main/GOVERNANCE.md)
is awaiting adoption; its voting/transition rules are not currently effective.
Follow CODE_OF_CONDUCT and use the SECURITY policy for sensitive findings. The
private reporting contacts in those drafts still need confirmation.

Release preparation does not authorize publishing packages, merging PRs, or
transferring repository ownership. Keep companion PRs linked for coordinated review.
