#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Benchmark ``bioheaders assess`` batch mode on a synthetic release (010 SC-004).

Builds a synthetic release in a temporary directory, by default 200 files:

- 10 genome FASTA files of 100 MB of sequence each (gzip and BGZF), which the
  pairs make the tool read completely (names, lengths, MD5, FHR checksum);
- 120 GFF3 and VCF files of 50-500 MB uncompressed each (gzip and BGZF), each
  paired with a genome in ``pairs.tsv``;
- 70 small GAF and protein FASTA files.

Genome sequences are pseudo-random, so they cost what real sequence costs to
decompress and hash. The other files have a header and 2,000 varied records,
then one record repeated in identical compressed members (gzip) or blocks
(BGZF): their uncompressed sizes are as stated, but they take little disk
space. The tool reads only their header and a sample of records (1,000 by
default), so their body size does not change the result (research R-14).

The script then runs ``bioheaders assess --recursive --pairs pairs.tsv
--output OUT RELEASE`` once, times it, runs it again into a second directory
and checks that the output is byte-identical, and prints the wall times and
the machine. It exits 1 if the first run takes 600 s or more (SC-004: 200
files in under 10 minutes on a laptop), or if the two runs differ. The data
are synthetic: names and values are labelled SYNTHETIC and identify nothing.
"""

import argparse
import gzip
import hashlib
import os
import platform
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

LIMIT_SECONDS = 600
MB = 1_000_000
SEQUENCES_PER_GENOME = 8
LINE = 60
ACGT = bytes(b"ACGT"[i % 4] for i in range(256))
BGZF_EOF = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")


def gzip_member(data):
    return gzip.compress(data, compresslevel=6, mtime=0)


def bgzf_block(data):
    compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
    deflated = compressor.compress(data) + compressor.flush()
    size = len(deflated) + 25
    header = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff\x06\x00BC\x02\x00"
    return (
        header
        + struct.pack("<H", size)
        + deflated
        + struct.pack("<II", zlib.crc32(data) & 0xFFFFFFFF, len(data))
    )


def bgzf_blocks(data, size=60_000):
    return b"".join(bgzf_block(data[i : i + size]) for i in range(0, len(data), size))


class Writer:
    """Write a gzip or BGZF file: a header, then a repeated body unit."""

    def __init__(self, path, compression):
        self.stream = open(path, "wb")
        self.compression = compression

    def write(self, data):
        if self.compression == "bgzf":
            self.stream.write(bgzf_blocks(data))
        else:
            self.stream.write(gzip_member(data))

    def repeat(self, unit, total):
        """Write ``unit`` (uncompressed) repeatedly until ``total`` bytes."""
        packed = bgzf_blocks(unit) if self.compression == "bgzf" else gzip_member(unit)
        for _ in range(max(1, total // len(unit))):
            self.stream.write(packed)

    def close(self):
        if self.compression == "bgzf":
            self.stream.write(BGZF_EOF)
        self.stream.close()


def genome(path, index, megabytes, compression):
    """Write a FASTA genome; return [(name, length)]."""
    rng = random.Random(index)
    total = megabytes * MB
    lengths = [total // SEQUENCES_PER_GENOME] * SEQUENCES_PER_GENOME
    names = [f"syn{index}_chr{n + 1}" for n in range(SEQUENCES_PER_GENOME)]
    writer = Writer(path, compression)
    for name, length in zip(names, lengths):
        writer.write(f">{name} SYNTHETIC benchmark sequence\n".encode())
        remaining = length
        while remaining:
            size = min(remaining, 6_000_000)
            sequence = rng.randbytes(size).translate(ACGT)
            lines = b"\n".join(
                sequence[i : i + LINE] for i in range(0, len(sequence), LINE)
            )
            writer.write(lines + b"\n")
            remaining -= size
    writer.close()
    return list(zip(names, lengths))


def gff3(path, sequences, megabytes, compression):
    header = ["##gff-version 3", "#!processor SYNTHETIC benchmark generator"]
    header += [f"##sequence-region {name} 1 {length}" for name, length in sequences]
    records = []
    for n in range(2000):
        name, length = sequences[n % len(sequences)]
        start = (n * 997) % (length - 2000) + 1
        records.append(
            f"{name}\tSYNTHETIC\tgene\t{start}\t{start + 1500}\t.\t+\t.\t"
            f"ID=gene{n};Name=SYNTHETIC{n}"
        )
    _text(path, header, records, megabytes, compression)


def vcf(path, sequences, megabytes, compression):
    header = ["##fileformat=VCFv4.3", "##source=SYNTHETIC benchmark generator"]
    header += [f"##contig=<ID={name},length={length}>" for name, length in sequences]
    header += [
        '##INFO=<ID=DP,Number=1,Type=Integer,Description="SYNTHETIC depth">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
    ]
    records = []
    for n in range(2000):
        name, length = sequences[n % len(sequences)]
        records.append(f"{name}\t{(n * 7919) % length + 1}\t.\tA\tG\t50\tPASS\tDP={n}")
    _text(path, header, records, megabytes, compression)


def gaf(path, megabytes, compression):
    header = ["!gaf-version: 2.2", "!generated-by: SYNTHETIC benchmark generator"]
    records = [
        f"SYN\tSYN{n}\tsyn{n}\t\tGO:0008150\tSYN:REF\tIEA\t\tP\t\t\tgene\ttaxon:0\t"
        "20260101\tSYN"
        for n in range(2000)
    ]
    _text(path, header, records, megabytes, compression)


def protein(path, megabytes, compression):
    records = []
    for n in range(500):
        records.append(f">SYNPROT{n} SYNTHETIC protein")
        records.append("MSYNTHETICPEPTIDE" * 4)
    _text(path, [], records, megabytes, compression)


def _text(path, header, records, megabytes, compression):
    """The header and varied records, then the last record repeated to the size."""
    writer = Writer(path, compression)
    head = "".join(line + "\n" for line in header).encode()
    sample = "".join(line + "\n" for line in records).encode()
    writer.write(head + sample)
    filler = (records[-1] + "\n").encode() * (MB // (len(records[-1]) + 1))
    writer.repeat(filler, megabytes * MB - len(head) - len(sample))
    writer.close()


def build(root, files, genome_mb):
    genomes = max(1, files // 20)
    derived = files * 3 // 5
    small = files - genomes - derived
    pairs = []
    sequences = []
    for index in range(genomes):
        compression = "bgzf" if index % 2 else "gzip"
        name = f"genome/synthetic{index:02d}.fa.gz"
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        sequences.append(genome(target, index, genome_mb, compression))
    for index in range(derived):
        size = 50 + (450 * index) // max(1, derived - 1)
        compression = "bgzf" if index % 2 else "gzip"
        parent = index % genomes
        if index % 12 < 7:
            name = f"annotation/synthetic{index:03d}.gff3.gz"
            maker = gff3
        else:
            name = f"variation/synthetic{index:03d}.vcf.gz"
            maker = vcf
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        maker(target, sequences[parent], size, compression)
        pairs.append((name, f"genome/synthetic{parent:02d}.fa.gz"))
    for index in range(small):
        compression = "bgzf" if index % 2 else "gzip"
        size = 1 + index % 20
        if index % 2:
            name, maker = f"go/synthetic{index:03d}.gaf.gz", gaf
        else:
            name, maker = f"protein/synthetic{index:03d}.pep.fa.gz", protein
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        maker(target, size, compression)
    with open(root.parent / "pairs.tsv", "w", encoding="utf-8", newline="\n") as out:
        out.write("# derived\trelated (SYNTHETIC benchmark)\n")
        for derived_path, related_path in pairs:
            out.write(f"{derived_path}\t{related_path}\n")
    return genomes, derived, small


def tree_digest(directory):
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode() + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def machine():
    model = platform.processor() or platform.machine()
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return (
        f"{model}; {os.cpu_count()} logical CPUs; {platform.system()} "
        f"{platform.release()}; Python {platform.python_version()}"
    )


def assess(release, pairs, output, jobs):
    command = [sys.executable, "-m", "bioheaders", "assess", "--recursive"]
    command += ["--pairs", str(pairs), "--output", str(output)]
    if jobs:
        command += ["--jobs", str(jobs)]
    start = time.monotonic()
    result = subprocess.run(command + [str(release)], capture_output=True, text=True)
    return time.monotonic() - start, result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--files", type=int, default=200, help="files (default 200)")
    parser.add_argument(
        "--genome-mb", type=int, default=100, help="MB of sequence per genome"
    )
    parser.add_argument("--jobs", type=int, help="passed to bioheaders assess --jobs")
    parser.add_argument(
        "--directory", help="work here instead of a temporary directory"
    )
    parser.add_argument("--keep", action="store_true", help="keep the generated files")
    args = parser.parse_args()
    if args.files < 3:
        parser.error("--files must be 3 or more")
    work = Path(args.directory or tempfile.mkdtemp(prefix="bench_assess."))
    release = work / "release"
    try:
        release.mkdir(parents=True)
        start = time.monotonic()
        genomes, derived, small = build(release, args.files, args.genome_mb)
        size = sum(p.stat().st_size for p in release.rglob("*") if p.is_file())
        print(
            f"generated {genomes + derived + small} files ({genomes} genomes of "
            f"{args.genome_mb} MB sequence, {derived} paired GFF3/VCF, {small} "
            f"GAF/protein FASTA; {size / MB:.0f} MB on disk) in "
            f"{time.monotonic() - start:.1f} s"
        )
        print(f"machine: {machine()}")
        first, result = assess(release, work / "pairs.tsv", work / "out1", args.jobs)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            print(f"bioheaders assess exited {result.returncode}", file=sys.stderr)
            return 1
        print(f"run 1: {first:.1f} s wall time")
        second, result = assess(release, work / "pairs.tsv", work / "out2", args.jobs)
        identical = tree_digest(work / "out1") == tree_digest(work / "out2")
        print(f"run 2: {second:.1f} s wall time; byte-identical: {identical}")
        verdict = first < LIMIT_SECONDS
        print(
            f"SC-004 ({args.files} files < {LIMIT_SECONDS} s): "
            f"{'pass' if verdict else 'FAIL'} ({first:.1f} s)"
        )
        return 0 if verdict and identical and result.returncode == 0 else 1
    finally:
        if args.keep:
            print(f"kept {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
