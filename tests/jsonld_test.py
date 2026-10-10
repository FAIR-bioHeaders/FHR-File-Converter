# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""JSON-LD writing and canonical reading (FHR-Specification feature 011).

These tests need no JSON-LD processor and run with network access disabled
(tests/conftest.py).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from bioheaders import fhr, jsonld

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.executable).parent
# A FHR-Specification checkout: $FHR_SPECIFICATION, or ../FHR-Specification.
SPEC = Path(os.environ.get("FHR_SPECIFICATION", ROOT.parent / "FHR-Specification"))
ORCID = "https://orcid.org/0000-0002-1825-0097"  # ORCID's documented example iD.
ROR = "https://ror.org/05gq02987"  # Used only to test the typing rule.
EXPORT = {
    "id": "https://example.org/datasets/synthetic-human",
    "url": "https://example.org/genomes/synthetic-human",
    "keywords": ["genome assembly", "Homo sapiens"],
}
NOT_CANONICAL = (
    "this JSON-LD is not in the canonical FAIR-bioHeaders form (rule J1 of "
    "FHR-Specification docs/JSONLD.md); reading other JSON-LD forms is not supported yet"
)


@pytest.fixture
def metadata():
    return json.loads((ROOT / "examples/example.fhr.json").read_text())


def run(*args, stdin=b"", cwd=None):
    return subprocess.run(
        [str(arg) for arg in args], input=stdin, capture_output=True, cwd=cwd
    )


def bioheaders_command(*args, **options):
    return run(BIN / "bioheaders", *args, **options)


def written(metadata, **options):
    return json.loads(fhr(**metadata).output_jsonld(**options))


def read(document, **options):
    data = fhr()
    data.input_jsonld(json.dumps(document), **options)
    return data.__dict__


def test_examples_are_byte_identical(metadata):
    for stem in ("example", "minimal"):
        source = json.loads((ROOT / f"examples/{stem}.fhr.json").read_text())
        expected = (ROOT / f"examples/{stem}.fhr.jsonld").read_text(encoding="utf-8")
        assert fhr(**source).output_jsonld() == expected


def test_writer_layout(metadata):
    document = written(metadata)
    assert list(document)[:2] == ["@context", "@type"]
    assert document["@context"] == jsonld.CONTEXT["@context"]
    assert document["@type"] == "Dataset"
    assert list(document)[2:] == list(metadata)
    assert list(document["taxon"]) == ["@type", "name", "uri"]
    assert document["taxon"]["@type"] == "Taxon"
    assert document["accessionID"]["@type"] == "PropertyValue"
    assert document["vitalStats"]["@type"] == "VitalStats"
    assert document["assemblySoftware"][0]["@type"] == "SoftwareApplication"
    assert document["metadataAuthor"][0]["@type"] == "Person"
    text = fhr(**metadata).output_jsonld()
    assert text == json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def test_author_typing_from_identifier(metadata):
    metadata["assemblyAuthor"] = [
        {"name": "Josiah Carberry", "uri": ORCID},
        {"name": "Example organization", "uri": ROR},
        {"name": "Name only"},
        {"name": "Other identifier", "uri": "https://example.org/people/1"},
    ]
    types = [item["@type"] for item in jsonld.to_jsonld(metadata)["assemblyAuthor"]]
    assert types == ["Person", "Organization", "Agent", "Agent"]
    assert read(written(metadata)) == metadata


def test_legacy_software_string_is_unchanged(metadata):
    metadata["assemblySoftware"] = "hifiasm"
    document = written(metadata)
    assert document["assemblySoftware"] == "hifiasm"
    assert read(document) == metadata


def test_documentation_text_or_url(metadata):
    assert "subjectOf" not in written(metadata)
    for value in ("https://example.org/genome/README", "ftp://example.org/readme.txt"):
        metadata["documentation"] = value
        document = written(metadata)
        assert "documentation" not in document
        assert document["subjectOf"] == value
        assert (
            list(document).index("subjectOf")
            == list(metadata).index("documentation") + 2
        )
        back = read(document)
        assert back == metadata and list(back) == list(metadata)
    for value in ("See https://example.org/readme", "example.org", "urn:x:readme"):
        metadata["documentation"] = value
        assert written(metadata)["documentation"] == value


def test_documentation_and_subject_of_together_are_rejected(metadata):
    document = written(metadata)
    document["subjectOf"] = "https://example.org/readme"
    with pytest.raises(ValueError, match="both documentation and subjectOf"):
        read(document)


def test_absent_optional_fields_stay_absent(metadata):
    minimal = json.loads((ROOT / "examples/minimal.fhr.json").read_text())
    document = written(minimal)
    assert set(document) - {"@context", "@type"} == set(minimal)
    assert "null" not in json.dumps(
        {k: v for k, v in document.items() if k != "@context"}
    )
    assert read(document) == minimal


def test_export_context(metadata):
    without = written(metadata)
    for key in ("@id", "keywords", "url", "conformsTo"):
        assert key not in without
    assert jsonld.bioschemas_missing(without) == ["@id", "keywords", "url"]
    document = written(metadata, export=EXPORT)
    assert list(document)[:3] == ["@context", "@type", "@id"]
    assert list(document)[-3:] == ["keywords", "url", "conformsTo"]
    assert document["conformsTo"] == jsonld.BIOSCHEMAS_DATASET_PROFILE
    assert document["conformsTo"].endswith("/Dataset/1.0-RELEASE")
    warnings = []
    data = fhr()
    data.input_jsonld(json.dumps(document), warn=warnings.append)
    assert data.__dict__ == metadata
    assert warnings == [
        f"JSON-LD: {key} is export metadata, not an FHR field; it was not kept"
        for key in ("@id", "keywords", "url", "conformsTo")
    ]


def test_incomplete_export_context_makes_no_claim(metadata):
    partial = {key: value for key, value in EXPORT.items() if key != "id"}
    document = written(metadata, export=partial)
    assert "conformsTo" not in document and "@id" not in document
    assert jsonld.bioschemas_missing(document) == ["@id"]
    del metadata["reuseConditions"]
    document = written(metadata, export=EXPORT)
    assert "conformsTo" not in document
    assert jsonld.bioschemas_missing(document) == ["license"]
    metadata["reuseConditions"] = "CC0-1.0"
    metadata["documentation"] = "https://example.org/readme"
    assert jsonld.bioschemas_missing(written(metadata, export=EXPORT)) == [
        "description"
    ]


@pytest.mark.parametrize(
    "export",
    [
        {"keyword": ["x"]},
        {"keywords": "genome"},
        {"keywords": []},
        {"keywords": [""]},
        {"url": "example.org"},
        {"id": 5},
        ["keywords"],
    ],
)
def test_export_context_is_validated(metadata, export):
    with pytest.raises(ValueError, match="export context"):
        jsonld.to_jsonld(metadata, export=export)


def test_unmapped_keys(metadata):
    assert jsonld.unmapped_keys(metadata) == []
    metadata["taxon"]["checksum"] = "nested"
    metadata["assemblyAuthor"][0]["affiliation"] = "Example institute"
    metadata["vitalStats"]["contigN50"] = 3
    assert jsonld.unmapped_keys(metadata) == [
        "taxon.checksum",
        "assemblyAuthor[0].affiliation",
        "vitalStats.contigN50",
    ]
    assert read(written(metadata)) == metadata


def test_keyword_like_keys_are_refused(metadata):
    metadata["taxon"]["@id"] = "https://example.org/taxon"
    with pytest.raises(ValueError, match=r"taxon\.@id"):
        jsonld.to_jsonld(metadata)


def test_canonical_reading_of_context_urls(metadata):
    assert jsonld.KNOWN_CONTEXT_URLS == (jsonld.RAW_MAIN_CONTEXT_URL,)
    for url in jsonld.KNOWN_CONTEXT_URLS:
        document = dict(written(metadata), **{"@context": url})
        assert jsonld.is_canonical(document)
        assert read(document) == metadata


def test_canonical_reading_sets_types_aside_at_every_depth(metadata):
    document = written(metadata)
    document["@type"] = ["Dataset", "https://example.org/Extra"]
    document["vitalStats"]["@type"] = "Anything"
    del document["taxon"]["@type"]
    assert jsonld.is_canonical(document)
    assert read(document) == metadata


def test_canonical_reading_keeps_extra_nested_keys(metadata):
    metadata["taxon"]["checksum"] = "nested property"
    assert read(written(metadata)) == metadata


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update({"@context": {"@vocab": "http://schema.org/"}}),
        lambda d: d.update({"@context": "https://schema.org/"}),
        lambda d: d.update({"@graph": []}),
        lambda d: d["taxon"].update({"@id": "https://identifiers.org/taxonomy:9606"}),
        lambda d: d.update({"@type": {"@id": "Dataset"}}),
        lambda d: d.update({"@id": 5}),
        lambda d: d.pop("@context"),
    ],
)
def test_non_canonical_documents_are_not_read(metadata, change):
    document = written(metadata)
    change(document)
    assert not jsonld.is_canonical(document)
    with pytest.raises(ValueError) as error:
        read(document)
    assert str(error.value) == NOT_CANONICAL


def test_non_object_documents_are_rejected():
    for text in ("[]", '"text"', "3"):
        with pytest.raises(ValueError):
            fhr().input_jsonld(text)


def test_duplicate_keys_are_rejected(metadata):
    text = (
        fhr(**metadata)
        .output_jsonld()
        .replace('"genome": ', '"genome": "first", "genome": ', 1)
    )
    with pytest.raises(ValueError, match="Duplicate JSON object key"):
        fhr().input_jsonld(text)


def test_missing_checksum_fails_schema_validation(metadata):
    del metadata["checksum"]
    data = fhr()
    data.input_jsonld(fhr(**metadata).output_jsonld())
    with pytest.raises(ValidationError):
        data.fhr_validate()


def test_utf8_bom_and_bytes_are_accepted(metadata):
    text = fhr(**metadata).output_jsonld()
    data = fhr()
    data.input_jsonld(("﻿" + text).encode("utf-8"))
    assert data.__dict__ == metadata


def test_convert_warns_about_nested_keys_without_terms(metadata, tmp_path):
    metadata["taxon"]["checksum"] = "nested property"
    source = tmp_path / "nested.json"
    source.write_text(json.dumps(metadata))
    output = tmp_path / "nested.jsonld"
    result = bioheaders_command("convert", source, output)
    assert result.returncode == 0, result.stderr
    assert result.stderr.decode() == (
        "FHR: JSON-LD: taxon.checksum has no JSON-LD term; linked-data consumers "
        "will ignore it\n"
    )
    assert json.loads(output.read_text())["taxon"]["checksum"] == "nested property"
    back = tmp_path / "back.json"
    assert bioheaders_command("convert", output, back).returncode == 0
    assert json.loads(back.read_text()) == metadata


def test_convert_with_export_context(metadata, tmp_path):
    source = ROOT / "examples/example.fhr.json"
    export = tmp_path / "export.yaml"
    export.write_text(
        "id: {id}\nurl: {url}\nkeywords:\n- genome assembly\n- Homo sapiens\n".format(
            **EXPORT
        )
    )
    output = tmp_path / "out.jsonld"
    result = bioheaders_command("convert", "--export-context", export, source, output)
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    document = json.loads(output.read_text())
    assert document["conformsTo"] == jsonld.BIOSCHEMAS_DATASET_PROFILE
    back = tmp_path / "back.json"
    result = bioheaders_command("convert", output, back)
    assert result.returncode == 0
    assert result.stderr.decode().count("is export metadata") == 4
    assert json.loads(back.read_text()) == metadata

    export.write_text("keywords: [genome assembly]\n")
    result = bioheaders_command("convert", "--export-context", export, source, output)
    assert result.returncode == 0, result.stderr
    assert result.stderr.decode() == (
        "FHR: JSON-LD: not claiming Bioschemas Dataset conformance; missing: @id, url\n"
    )
    assert "conformsTo" not in json.loads(output.read_text())

    for content, message in (
        ("keywords: genome\n", "export context"),
        ("unknown: 1\n", "export context"),
    ):
        export.write_text(content)
        result = bioheaders_command(
            "convert", "--export-context", export, source, output
        )
        assert result.returncode == 1
        assert message in result.stderr.decode()
    result = bioheaders_command(
        "convert", "--export-context", export, source, tmp_path / "out.json"
    )
    assert result.returncode == 1
    assert b"--export-context applies only to JSON-LD output" in result.stderr


def test_validate_and_stdin(metadata, tmp_path):
    source = ROOT / "examples/example.fhr.jsonld"
    result = bioheaders_command("validate", source)
    assert result.returncode == 0 and result.stdout == b"FHR metadata is valid.\n"
    piped = bioheaders_command(
        "convert",
        "-",
        "-",
        "--from",
        "jsonld",
        "--to",
        "json",
        stdin=source.read_bytes(),
    )
    assert piped.returncode == 0, piped.stderr
    assert json.loads(piped.stdout) == metadata
    piped = bioheaders_command(
        "convert",
        "-",
        "-",
        "--from",
        "json",
        "--to",
        "jsonld",
        stdin=(ROOT / "examples/example.fhr.json").read_bytes(),
    )
    assert piped.stdout == source.read_bytes()
    invalid = tmp_path / "invalid.jsonld"
    del metadata["checksum"]
    invalid.write_text(fhr(**metadata).output_jsonld())
    result = bioheaders_command("validate", invalid)
    assert result.returncode == 1
    assert b"schema validation failed" in result.stderr


def test_context_matches_the_specification():
    published = SPEC / "jsonld" / "fhr.context.jsonld"
    if not published.is_file():
        pytest.skip("FHR-Specification checkout with jsonld/ not found")
    bundled = ROOT / "bioheaders" / "fhr.context.jsonld"
    assert bundled.read_bytes() == published.read_bytes()
    for stem in ("example", "minimal"):
        name = f"examples/{stem}.fhr.jsonld"
        assert (ROOT / name).read_bytes() == (SPEC / name).read_bytes()
