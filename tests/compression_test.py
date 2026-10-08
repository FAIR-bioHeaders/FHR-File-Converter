"""Gzip/BGZF input and output, and stdin/stdout use of the commands."""

import gzip
import io
import json
import random
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from fhr import fhr, read_chunks
from fhr.cli import (
    BGZF_BLOCK_SIZE,
    BGZF_EOF,
    BgzfWriter,
    SequenceScan,
    checksum,
    combine,
    open_input,
)

ROOT = Path(__file__).resolve().parents[1]
BODIES = {
    "fasta": b">ctg\nACGT\nAC\n; comment\n>two\nGG\n",
    "gfa": b"H\tVN:Z:1.0\nS\tctg\tACGT\nL\tctg\t+\tctg\t+\t0M\n",
}


@pytest.fixture(scope="module")
def metadata():
    return json.loads((ROOT / "examples/example.fhr.json").read_text())


def command(tmp_path, script, *args, stdin=b""):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *map(str, args)],
        cwd=tmp_path,
        capture_output=True,
        input=stdin,
    )


def bgzf(data):
    output = io.BytesIO()
    writer = BgzfWriter(output)
    writer.write(data)
    writer.close()
    return output.getvalue()


def compressions(content):
    middle = len(content) // 2
    return {
        "gzip-1": gzip.compress(content, compresslevel=1),
        "gzip-9": gzip.compress(content, compresslevel=9),
        "multi-member": gzip.compress(content[:middle])
        + gzip.compress(content[middle:]),
        "bgzf": bgzf(content),
    }


def scan(path, kind):
    with open_input(path) as stream:
        result = SequenceScan(read_chunks(stream), kind)
    return result.checksum(), result.header


def crlf_file(content, kind):
    """Return ``content`` with CRLF line endings and its checksum updated."""
    crlf = content.replace(b"\n", b"\r\n")
    data = fhr()
    getattr(data, "input_" + kind)(content)
    return crlf.replace(data.checksum.encode(), checksum(crlf, kind).encode())


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
@pytest.mark.parametrize("crlf", [False, True])
def test_compressed_input_matches_plain(metadata, tmp_path, kind, crlf):
    body = BODIES[kind]
    content = combine(fhr(**metadata), body, kind)
    if crlf:
        content = crlf_file(content, kind)
        body = body.replace(b"\n", b"\r\n")
    plain = tmp_path / ("plain." + kind)
    plain.write_bytes(content)
    expected = scan(plain, kind)
    # Plain bytes in a .gz file are read as plain bytes.
    misnamed = tmp_path / f"plain.{kind}.gz"
    misnamed.write_bytes(content)
    assert scan(misnamed, kind) == expected
    assert command(tmp_path, f"{kind}/fhr_{kind}_validate.py", plain).returncode == 0
    reference = tmp_path / "plain.json"
    assert command(tmp_path, "fhr_convert.py", plain, reference).returncode == 0
    for name, compressed in compressions(content).items():
        # Detection uses the magic bytes, so the extension does not matter.
        for path in (tmp_path / f"{name}.{kind}.gz", tmp_path / f"{name}.{kind}"):
            path.write_bytes(compressed)
            assert scan(path, kind) == expected, name
            result = command(tmp_path, f"{kind}/fhr_{kind}_validate.py", path)
            assert result.returncode == 0, (name, result.stderr)
            output = tmp_path / f"{name}.json"
            result = command(tmp_path, "fhr_convert.py", path, output)
            assert result.returncode == 0, result.stderr
            assert output.read_bytes() == reference.read_bytes()
            stripped = command(tmp_path, f"{kind}/fhr_{kind}_strip.py", path)
            assert stripped.stdout == body


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
def test_combine_to_gz_then_validate_and_strip(metadata, tmp_path, kind):
    body = BODIES[kind] * 5000
    source = tmp_path / "input.yaml"
    source.write_bytes((ROOT / "examples/example.fhr.yaml").read_bytes())
    sequence = tmp_path / ("sequence." + kind)
    sequence.write_bytes(body)
    plain = tmp_path / ("plain." + kind)
    compressed = tmp_path / (f"combined.{kind}.gz")
    combine_script = f"{kind}/fhr_{kind}_combine.py"
    assert (
        command(tmp_path, combine_script, source, sequence, "-o", plain).returncode == 0
    )
    result = command(tmp_path, combine_script, source, sequence, "-o", compressed)
    assert result.returncode == 0, result.stderr
    assert compressed.read_bytes()[:4] == b"\x1f\x8b\x08\x04"
    assert gzip.decompress(compressed.read_bytes()) == plain.read_bytes()
    validate = f"{kind}/fhr_{kind}_validate.py"
    assert command(tmp_path, validate, compressed).returncode == 0
    strip = f"{kind}/fhr_{kind}_strip.py"
    assert command(tmp_path, strip, compressed).stdout == body
    stripped = tmp_path / f"stripped.{kind}.bgz"
    assert command(tmp_path, strip, compressed, stripped).returncode == 0
    assert gzip.decompress(stripped.read_bytes()) == body
    # Compressed input keeps its compression extension in the default output.
    result = command(tmp_path, combine_script, source, stripped)
    assert result.returncode == 0, result.stderr
    default = tmp_path / f"stripped.fhr.{kind}.bgz"
    assert gzip.decompress(default.read_bytes()) == plain.read_bytes()
    # Metadata output to a .gz path is compressed too.
    reference = tmp_path / "metadata.json"
    output = tmp_path / "metadata.json.gz"
    assert command(tmp_path, "fhr_convert.py", plain, reference).returncode == 0
    assert command(tmp_path, "fhr_convert.py", compressed, output).returncode == 0
    assert gzip.decompress(output.read_bytes()) == reference.read_bytes()


def parse_bgzf(content):
    """Return the uncompressed blocks of BGZF bytes, checking each block."""
    blocks = []
    position = 0
    while position < len(content):
        header = content[position : position + 18]
        fields = struct.unpack("<4BI2BH2BHH", header)
        assert fields[:4] == (0x1F, 0x8B, 8, 4)
        assert fields[7:11] == (6, ord("B"), ord("C"), 2)
        size = fields[11] + 1
        assert size <= 65536
        block = content[position : position + size]
        assert len(block) == size
        data = zlib.decompress(block[18:-8], -15)
        crc, length = struct.unpack("<II", block[-8:])
        assert crc == zlib.crc32(data) and length == len(data)
        assert len(data) <= BGZF_BLOCK_SIZE
        blocks.append((block, data))
        position += size
    return blocks


def test_bgzf_structure():
    random.seed(0)
    noise = bytes(random.getrandbits(8) for _ in range(150000))
    data = b"ACGT" * 50000 + noise + b"\n"
    output = io.BytesIO()
    writer = BgzfWriter(output)
    # Writes of varied sizes are buffered into full blocks.
    position = 0
    for size in [1, 2, 70000, 65279, 3, 200000, len(data)]:
        writer.write(data[position : position + size])
        position += size
    writer.close()
    content = output.getvalue()
    blocks = parse_bgzf(content)
    assert blocks[-1] == (BGZF_EOF, b"")
    assert len(BGZF_EOF) == 28
    assert [len(block) for _, block in blocks[:-2]] == [BGZF_BLOCK_SIZE] * (
        len(blocks) - 2
    )
    assert b"".join(block for _, block in blocks) == data
    assert gzip.decompress(content) == data
    assert bgzf(b"") == BGZF_EOF


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
def test_corrupt_gzip_is_a_clean_error(metadata, tmp_path, kind):
    content = combine(fhr(**metadata), BODIES[kind] * 1000, kind)
    compressed = gzip.compress(content)
    flipped = bytearray(compressed)
    flipped[len(flipped) // 2] ^= 0xFF
    crc = bytearray(compressed)
    crc[-6] ^= 0xFF
    cases = {
        "truncated": compressed[: len(compressed) // 2],
        "header only": compressed[:5],
        "corrupt data": bytes(flipped),
        "bad crc": bytes(crc),
        "trailing garbage": compressed + b"garbage",
    }
    source = tmp_path / "input.json"
    source.write_text(json.dumps(metadata))
    for name, data in cases.items():
        path = tmp_path / f"bad.{kind}.gz"
        path.write_bytes(data)
        output = tmp_path / ("output." + kind)
        for script, args in (
            (f"{kind}/fhr_{kind}_validate.py", [path]),
            (f"{kind}/fhr_{kind}_strip.py", [path]),
            (f"{kind}/fhr_{kind}_strip.py", [path, output]),
            (f"{kind}/fhr_{kind}_combine.py", [source, path, "-o", output]),
            ("fhr_convert.py", [path, tmp_path / "output.json"]),
        ):
            result = command(tmp_path, script, *args)
            assert result.returncode == 1, (name, script)
            message = result.stderr.decode()
            assert message.startswith(f"FHR: Invalid gzip input {path}: "), (
                name,
                message,
            )
            assert message.count("\n") == 1
            assert result.stdout == b""
        stdin = command(tmp_path, f"{kind}/fhr_{kind}_validate.py", "-", stdin=data)
        assert stdin.returncode == 1
        assert stdin.stderr.decode().startswith("FHR: Invalid gzip input <stdin>: ")
        assert not output.exists()
        assert not (tmp_path / "output.json").exists()


@pytest.mark.parametrize("kind", ["fasta", "gfa"])
@pytest.mark.parametrize("compress", [False, True])
def test_stdin_and_stdout(metadata, tmp_path, kind, compress):
    body = BODIES[kind] * 3000
    content = combine(fhr(**metadata), body, kind)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(metadata))

    def stdin(data):
        return gzip.compress(data) if compress else data

    validate = f"{kind}/fhr_{kind}_validate.py"
    result = command(tmp_path, validate, "-", stdin=stdin(content))
    assert result.returncode == 0, result.stderr
    assert result.stdout == b"Checksum verified.\n"
    tampered = content.replace(b"ACGT", b"ACGA", 1)
    assert command(tmp_path, validate, "-", stdin=stdin(tampered)).returncode == 1

    strip = f"{kind}/fhr_{kind}_strip.py"
    for args in (["-"], ["-", "-"]):
        result = command(tmp_path, strip, *args, stdin=stdin(content))
        assert result.returncode == 0 and result.stdout == body
    output = tmp_path / ("stripped." + kind)
    assert command(tmp_path, strip, "-", output, stdin=stdin(content)).returncode == 0
    assert output.read_bytes() == body

    combine_script = f"{kind}/fhr_{kind}_combine.py"
    result = command(tmp_path, combine_script, source, "-", stdin=stdin(body))
    assert result.returncode == 0, result.stderr
    assert result.stdout == content
    result = command(
        tmp_path, combine_script, source, "-", "-o", "-", stdin=stdin(content)
    )
    assert result.stdout == content
    sequence = tmp_path / ("sequence." + kind)
    sequence.write_bytes(body)
    result = command(tmp_path, combine_script, source, sequence, "-o", "-")
    assert result.stdout == content
    compressed = tmp_path / f"combined.{kind}.gz"
    result = command(
        tmp_path, combine_script, source, "-", "-o", compressed, stdin=stdin(body)
    )
    assert result.returncode == 0, result.stderr
    assert gzip.decompress(compressed.read_bytes()) == content
    late = content + (b";~" if kind == "fasta" else b"#~") + b"x: 1\n"
    result = command(tmp_path, combine_script, source, "-", stdin=stdin(late))
    assert result.returncode == 1 and result.stdout == b""

    result = command(
        tmp_path,
        "fhr_convert.py",
        "-",
        "-",
        "--from",
        kind,
        "--to",
        "json",
        stdin=stdin(content),
    )
    assert result.returncode == 0, result.stderr
    expected = fhr()
    getattr(expected, "input_" + kind)(content)
    assert result.stdout.decode() == expected.output_json()
    result = command(tmp_path, "fhr_convert.py", source, "-", "--to", "yaml")
    assert result.stdout.decode() == fhr(**metadata).output_yaml()
    result = command(
        tmp_path,
        "fhr_validate.py",
        "-",
        "--from",
        "json",
        stdin=stdin(source.read_bytes()),
    )
    assert result.returncode == 0, result.stderr
    result = command(tmp_path, "fhr_convert.py", "-", "out.json", stdin=content)
    assert result.returncode == 1
    assert result.stderr.startswith(b"FHR: Give the format of - with --from")
    assert result.stdout == b""
