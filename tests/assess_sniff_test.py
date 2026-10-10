# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Input sniffing for the assessment: compression, format and scope (T006)."""

import gzip
import io
import tarfile

import pytest

from bioheaders.assess.sniff import SNIFF_BYTES, sniff
from bioheaders.cli import BgzfWriter

GFF3 = (
    b"##gff-version 3\n##sequence-region I 1 100\nI\tsrc\tgene\t1\t10\t.\t+\t.\tID=g1\n"
)
VCF = b"##fileformat=VCFv4.3\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"


def _gzip(data):
    return gzip.compress(data, mtime=0)


def _bgzf(data):
    output = io.BytesIO()
    writer = BgzfWriter(output)
    writer.write(data)
    writer.close()
    return output.getvalue()


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


@pytest.mark.parametrize("name", ["a.gff3", "a.gff3.gz", "a.txt", "GCF_000001405.40"])
def test_gzip_and_bgzf_are_detected_by_magic_bytes(tmp_path, name):
    assert sniff(_write(tmp_path, name, _gzip(GFF3))).compression == "gzip"
    assert sniff(_write(tmp_path, name, _bgzf(GFF3))).compression == "bgzf"
    assert sniff(_write(tmp_path, name, GFF3)).compression == "none"


def test_dbsnp_style_name_without_vcf_extension_is_vcf_by_content(tmp_path):
    result = sniff(_write(tmp_path, "GCF_000001405.40.gz", _bgzf(VCF)))
    assert (result.format, result.format_source, result.scope) == (
        "vcf",
        "content",
        "assessed",
    )


@pytest.mark.parametrize(
    "content, expected",
    [
        (GFF3, "gff3"),
        (b"# WormBase release WS298\n##gff-version 3\n", "gff3"),
        (VCF, "vcf"),
        (b"!gaf-version: 2.2\n!generated-by: GOC\n", "gaf"),
        (b">I\nACGT\n", "fasta"),
        (b";~schema: x\n;~checksum: y\n>c\nAC\n", "fasta"),
        (b"#~schema: x\nH\tVN:Z:1.0\nS\ts1\tACGT\n", "gfa"),
        (b"% a matlab style comment\n1 2 3\n", "unknown-text"),
    ],
)
def test_format_from_content(tmp_path, content, expected):
    result = sniff(_write(tmp_path, "data.txt", content))
    assert (result.format, result.format_source) == (expected, "content")


def test_format_from_extension_when_content_is_not_decisive(tmp_path):
    result = sniff(_write(tmp_path, "notes.gaf.gz", _gzip(b"! a free comment\n")))
    assert (result.format, result.format_source) == ("gaf", "extension")


def test_type_option_overrides_detection(tmp_path):
    result = sniff(_write(tmp_path, "a.gff3", GFF3), "vcf")
    assert (result.format, result.format_source) == ("vcf", "option")


def test_tar_inside_gzip_is_an_archive(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        info = tarfile.TarInfo("dmel.gff")
        info.size = len(GFF3)
        tar.addfile(info, io.BytesIO(GFF3))
    result = sniff(_write(tmp_path, "dmel.gff.gz", _gzip(buffer.getvalue())))
    assert (result.compression, result.format, result.scope) == (
        "gzip",
        "archive",
        "out_of_scope",
    )


@pytest.mark.parametrize(
    "magic, compress",
    [
        (b"BAM\x01", True),
        (b"CRAM\x03\x00", False),
        (bytes.fromhex("26fc8f88"), False),  # BigWig 0x888FFC26
        (bytes.fromhex("ebf28987"), False),  # BigBed 0x8789F2EB
    ],
)
def test_binary_magic_numbers(tmp_path, magic, compress):
    content = magic + b"\x00" * 60
    if compress:
        content = _bgzf(content)
    result = sniff(_write(tmp_path, "stub.bin", content))
    assert (result.format, result.scope) == ("binary", "out_of_scope")


def test_nul_bytes_in_the_first_64_kib_mean_binary(tmp_path):
    content = b"#" + b"a" * 1000 + b"\x00" + b"\n"
    assert sniff(_write(tmp_path, "x.gff3", content)).format == "binary"
    late = b"##gff-version 3\n" + b"#" * SNIFF_BYTES + b"\x00\n"
    assert sniff(_write(tmp_path, "y.gff3", late)).format == "gff3"


def test_sniff_reads_at_most_64_kib(tmp_path, monkeypatch):
    path = _write(tmp_path, "big.gff3", GFF3 + b"#" * (4 * SNIFF_BYTES))
    result = sniff(path)
    assert result.bytes_read <= SNIFF_BYTES


def test_corrupt_gzip_is_an_error(tmp_path):
    path = _write(tmp_path, "bad.gff3.gz", _gzip(GFF3)[:20] + b"garbage")
    result = sniff(path)
    assert result.scope == "error"
    assert "gzip" in result.error
