# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Serialise assessment reports (contracts/cli.md "Outputs", research R-12)."""

import json

from jsonschema import Draft202012Validator, FormatChecker

from . import data


def _check_no_floats(value, path="$"):
    if isinstance(value, float):
        raise ValueError(f"assessment report contains a float at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _check_no_floats(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_no_floats(item, f"{path}[{index}]")


def validate_report(report):
    """Raise ``ValueError`` unless ``report`` conforms to the report schema."""
    schema = data.load().report_schema
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            report
        ),
        key=lambda error: error.json_path,
    )
    if errors:
        error = errors[0]
        raise ValueError(
            f"assessment report does not conform at {error.json_path}: {error.message}"
        )
    _check_no_floats(report)


def to_json(report):
    """Return the report as JSON text: sorted keys, UTF-8, LF, trailing newline."""
    validate_report(report)
    return json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
