import base64
import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from fhr import SCHEMA, fhr
from fhr.cli import checksum, combine, strip_header

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def metadata():
    return json.loads((ROOT / "examples/example.fhr.json").read_text())


@pytest.mark.parametrize("kind", ["json", "yaml", "fasta", "gfa", "microdata"])
def test_round_trip(metadata, kind):
    metadata.update(
        assemblySoftware=[
            {
                "name": 'tool <x> & "quoted"',
                "version": "1.0",
                "commandLineOption": ["--threads", "2"],
            }
        ],
        assemblyProtocol="https://example.org/protocol",
        seqcol_id="A" * 32,
        vitalStats={"N90": 10, "gcContent": 42.5},
        relatedLink=[],
        funding="",
    )
    original = fhr(**metadata)
    loaded = fhr()
    getattr(loaded, "input_" + kind)(getattr(original, "output_" + kind)())
    assert loaded.__dict__ == metadata
    loaded.fhr_validate()


def test_minimal_and_optional_fields(metadata):
    minimal = {key: metadata[key] for key in SCHEMA["required"]}
    instance = fhr(**minimal)
    instance.fhr_validate()
    for kind in ("json", "yaml", "fasta", "gfa", "microdata"):
        loaded = fhr()
        getattr(loaded, "input_" + kind)(getattr(instance, "output_" + kind)())
        assert loaded.__dict__ == minimal
    other = fhr()
    other.input_json(instance.output_json())
    other.genome = "other"
    assert instance.genome != other.genome


@pytest.mark.parametrize(
    "field,value",
    [
        ("dateCreated", "2026-02-30"),
        ("seqcol_id", "invalid"),
        ("seqcol_id", "A" * 32 + "\n"),
        ("relatedLink", ["not a URI"]),
        ("vitalStats", {"gcContent": 101}),
        ("assemblySoftware", [{"version": "1"}]),
    ],
)
def test_validation_rejects_invalid_fields(metadata, field, value):
    metadata[field] = value
    with pytest.raises(ValidationError):
        fhr(**metadata).fhr_validate()


def test_legacy_software_and_yaml_dates(metadata):
    metadata["assemblySoftware"] = "HiFiASM"
    data = fhr(**metadata)
    data.fhr_validate()
    text = data.output_yaml().replace(
        "dateCreated: '2022-03-21'", "dateCreated: 2022-03-21"
    )
    loaded = fhr()
    loaded.input_yaml(text)
    assert loaded.dateCreated == "2022-03-21"
    loaded.fhr_validate()


@pytest.mark.parametrize(
    "kind,body",
    [
        ("fasta", b"; ordinary comment\r\n>ctg\r\nACGT\r\n"),
        ("gfa", b"# ordinary comment\r\nH\tVN:Z:1.0\r\nS\tctg\tACGT\r\n"),
    ],
)
def test_combine_strip_and_checksum_preserve_bytes(metadata, kind, body):
    original = deepcopy(metadata)
    combined = combine(fhr(**metadata), body, kind)
    assert strip_header(combined, kind) == body
    assert metadata == original
    loaded = fhr()
    getattr(loaded, "input_" + kind)(combined)
    assert checksum(combined, kind) == loaded.checksum
    prefix = b";~" if kind == "fasta" else b"#~"
    covered = b"".join(
        line
        for line in combined.splitlines(keepends=True)
        if not line.startswith(prefix + b"checksum:")
    )
    expected = base64.b64encode(hashlib.new("sha512_256", covered).digest()).decode()
    assert expected == loaded.checksum
    assert checksum(combined.replace(b"ACGT", b"ACGA"), kind) != expected
    assert (
        checksum(combined.replace(b"genome: ", b"genome: changed "), kind) != expected
    )
    assert strip_header(combine(loaded, combined, kind), kind) == body


def test_checksum_line_is_required_and_unique():
    with pytest.raises(ValueError, match="exactly one"):
        checksum(b">ctg\nACGT\n", "fasta")
    with pytest.raises(ValueError, match="exactly one"):
        checksum(b";~checksum: one\n;~checksum: two\n", "fasta")


def test_invalid_inputs():
    with pytest.raises(ValueError):
        fhr().input_yaml("- list")
    with pytest.raises(ValueError):
        fhr().input_fasta(">ctg\nACGT")
    with pytest.raises(ValueError):
        fhr().input_microdata("<html>no metadata</html>")


def command(tmp_path, script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *map(str, args)],
        cwd=tmp_path,
        capture_output=True,
    )


def test_cli_all_formats_and_sequence_helpers(metadata, tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(metadata))
    for extension in ("yaml", "json", "fasta", "gfa", "html"):
        output = tmp_path / ("output." + extension)
        result = command(tmp_path, "fhr_convert.py", source, output)
        assert result.returncode == 0, result.stderr
        assert command(tmp_path, "fhr_validate.py", output).returncode == 0
    for kind, payload in (("fasta", b">ctg\r\nACGT\r\n"), ("gfa", b"S\tctg\tACGT\r\n")):
        sequence = tmp_path / ("sequence." + kind)
        sequence.write_bytes(payload)
        combined = tmp_path / ("combined." + kind)
        result = command(
            tmp_path, f"{kind}/fhr_{kind}_combine.py", source, sequence, "-o", combined
        )
        assert result.returncode == 0, result.stderr
        assert (
            command(tmp_path, f"{kind}/fhr_{kind}_validate.py", combined).returncode
            == 0
        )
        stripped = tmp_path / ("stripped." + kind)
        assert (
            command(
                tmp_path, f"{kind}/fhr_{kind}_strip.py", combined, stripped
            ).returncode
            == 0
        )
        assert stripped.read_bytes() == payload
        assert (
            command(tmp_path, f"{kind}/fhr_{kind}_strip.py", combined).stdout == payload
        )
        combined.write_bytes(combined.read_bytes().replace(b"ACGT", b"ACGA"))
        assert (
            command(tmp_path, f"{kind}/fhr_{kind}_validate.py", combined).returncode
            == 1
        )


def test_cli_errors_do_not_overwrite_output(metadata, tmp_path):
    source = tmp_path / "bad.json"
    source.write_text('{"genome": "missing everything"}')
    output = tmp_path / "output.yaml"
    output.write_text("keep me")
    result = command(tmp_path, "fhr_convert.py", source, output)
    assert result.returncode == 1
    assert output.read_text() == "keep me"


def test_installed_entry_points_outside_checkout(tmp_path):
    bin_path = Path(sys.executable).parent
    for name in (
        "fhr-convert",
        "fhr-validate",
        "fhr-fasta-combine",
        "fhr-fasta-strip",
        "fhr-fasta-validate",
        "fhr-gfa-combine",
        "fhr-gfa-strip",
        "fhr-gfa-validate",
    ):
        result = subprocess.run(
            [str(bin_path / name), "--version"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "0.3.0"
    result = subprocess.run(
        [str(bin_path / "fhr-validate"), str(ROOT / "examples/minimal.fhr.json")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_bundled_schema_and_all_examples(metadata):
    assert SCHEMA == json.loads((ROOT / "fhr_schema.json").read_text())
    from fhr.cli import read_metadata

    for path in (ROOT / "examples").iterdir():
        data = read_metadata(path)
        data.fhr_validate()
        if path.suffix in {".fasta", ".gfa"}:
            kind = "fasta" if path.suffix == ".fasta" else "gfa"
            assert checksum(path.read_bytes(), kind) == data.checksum
        if path.name.startswith("example"):
            original = deepcopy(metadata)
            loaded = deepcopy(data.__dict__)
            original.pop("checksum")
            loaded.pop("checksum")
            assert loaded == original


def test_input_rejects_nonfinite_values_and_nonstring_keys():
    with pytest.raises(ValueError):
        fhr().input_json('{"vitalStats": {"gcContent": NaN}}')
    with pytest.raises(ValueError):
        fhr().input_yaml("vitalStats:\n  1: bad key\n")


def test_microdata_preserves_string_whitespace_and_unicode(metadata):
    metadata["documentation"] = '  α <tag> & "quoted"\nline two  '
    instance = fhr(**metadata)
    loaded = fhr()
    loaded.input_microdata(instance.output_microdata())
    assert loaded.documentation == metadata["documentation"]


def test_microdata_rejects_multiple_roots(metadata):
    instance = fhr(**metadata)
    with pytest.raises(ValueError, match="Multiple"):
        fhr().input_microdata(instance.output_microdata() * 2)


def test_microdata_recognizes_all_void_elements(metadata):
    metadata["documentation"] = "leftright"
    instance = fhr(**metadata)
    html = instance.output_microdata().replace(
        "leftright</span>",
        "left"
        + "".join(
            f"<{tag}>"
            for tag in (
                "area",
                "base",
                "br",
                "col",
                "embed",
                "hr",
                "img",
                "input",
                "link",
                "meta",
                "param",
                "source",
                "track",
                "wbr",
            )
        )
        + "right</span>",
    )
    loaded = fhr()
    loaded.input_microdata(html)
    assert loaded.documentation == "leftright"


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
def test_sequence_headers_preserve_unicode_line_separators(metadata, kind):
    metadata["documentation"] = "before\u2028middle\u2029after"
    instance = fhr(**metadata)
    header = getattr(instance, "output_" + kind)()
    assert "\u2028" in header
    assert "\u2029" in header
    loaded = fhr()
    body = ">ctg\nACGT\n" if kind == "fasta" else "S\tctg\tACGT\n"
    getattr(loaded, "input_" + kind)(header + body)
    assert loaded.documentation == metadata["documentation"]


def test_unsupported_hash_reports_runtime_requirement(monkeypatch):
    def unavailable(name):
        raise ValueError("unsupported hash")

    monkeypatch.setattr(hashlib, "new", unavailable)
    with pytest.raises(ValueError, match="Python distribution with OpenSSL"):
        checksum(b";~checksum: placeholder\n>ctg\nACGT\n", "fasta")


def test_nested_checksum_names_stay_covered(metadata):
    metadata["accessionID"]["checksum"] = "nested-value"
    combined = combine(fhr(**metadata), b">ctg\nACGT\n", "fasta")
    original = checksum(combined, "fasta")
    assert (
        checksum(combined.replace(b"nested-value", b"changed-value"), "fasta")
        != original
    )


def test_root_indentation_for_checksum_line():
    first = b";~ schema: example\n;~ checksum: placeholder\n;~ documentation: |\n;~   checksum: nested\n>ctg\nACGT\n"
    assert checksum(first, "fasta") != checksum(
        first.replace(b"nested", b"changed"), "fasta"
    )


@pytest.mark.parametrize(("kind", "prefix"), [("fasta", b";~"), ("gfa", b"#~")])
def test_checksum_root_indentation_ignores_yaml_markers(kind, prefix):
    content = (
        prefix
        + b"%YAML 1.2\n"
        + prefix
        + b"--- # metadata\n"
        + prefix
        + b" schema: example\n"
        + prefix
        + b" checksum: placeholder\n"
        + b">ctg\nACGT\n"
    )
    digest = checksum(content, kind)
    assert digest != checksum(content.replace(b"ACGT", b"ACGA"), kind)
    assert digest != checksum(content.replace(b"%YAML 1.2", b"%YAML 1.1"), kind)
    assert digest != checksum(
        content.replace(b"--- # metadata", b"--- # changed"), kind
    )


def test_cli_same_path_preserves_input(metadata, tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(metadata))
    original = source.read_bytes()
    result = command(tmp_path, "fhr_convert.py", source, source)
    assert result.returncode == 1
    assert source.read_bytes() == original


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
def test_cli_hardlinked_outputs_preserve_inputs(metadata, tmp_path, kind):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(metadata))
    conversion_link = tmp_path / "conversion.yaml"
    os.link(source, conversion_link)
    original = source.read_bytes()
    result = command(tmp_path, "fhr_convert.py", source, conversion_link)
    assert result.returncode == 1
    assert source.read_bytes() == original
    assert conversion_link.read_bytes() == original

    sequence = tmp_path / ("sequence." + kind)
    sequence.write_bytes(b">ctg\nACGT\n" if kind == "fasta" else b"S\tctg\tACGT\n")
    for linked_input in (source, sequence):
        output = tmp_path / f"combined-{linked_input.name}.{kind}"
        os.link(linked_input, output)
        before = linked_input.read_bytes()
        result = command(
            tmp_path,
            f"{kind}/fhr_{kind}_combine.py",
            source,
            sequence,
            "-o",
            output,
        )
        assert result.returncode == 1
        assert linked_input.read_bytes() == before
        assert output.read_bytes() == before

    combined = tmp_path / f"combined.{kind}"
    result = command(
        tmp_path,
        f"{kind}/fhr_{kind}_combine.py",
        source,
        sequence,
        "-o",
        combined,
    )
    assert result.returncode == 0, result.stderr
    strip_link = tmp_path / f"strip-link.{kind}"
    os.link(combined, strip_link)
    before = combined.read_bytes()
    result = command(tmp_path, f"{kind}/fhr_{kind}_strip.py", combined, strip_link)
    assert result.returncode == 1
    assert combined.read_bytes() == before
    assert strip_link.read_bytes() == before


def test_standard_microdata_properties(metadata):
    instance = fhr(**metadata)
    html = instance.output_microdata()
    html = html.replace(
        '<span itemprop="schemaVersion" data-fhr-type="number">1.0</span>',
        '<meta itemprop="schemaVersion" content="1.0">',
    )
    html = html.replace(
        '<span itemprop="assemblyProtocol" data-fhr-type="string">https://example.org/assembly-protocol</span>',
        '<a itemprop="assemblyProtocol" href="https://example.org/assembly-protocol"></a>',
    )
    loaded = fhr()
    loaded.input_microdata(html)
    assert loaded.__dict__ == metadata
