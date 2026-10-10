# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Batch mode of ``bioheaders assess`` (010 US4, T048; contracts/cli.md)."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from assess_helpers import FIXTURES, REFSEQ_GFF3

from bioheaders.assess import assess_release
from bioheaders.assess.data import load

PAIRS = FIXTURES / "pairs"
SYMBOLS = {"E", "P", "N", "NA", "NAS"}
STATUSES = (
    "evidenced",
    "partially_evidenced",
    "not_evidenced",
    "not_applicable",
    "not_assessed",
)


def bioheaders(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "bioheaders", *map(str, args)],
        capture_output=True,
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )


@pytest.fixture
def release(tmp_path):
    """A small release tree with a genome, paired annotations and a hidden file."""
    root = tmp_path / "release"
    (root / "genome").mkdir(parents=True)
    (root / "annotation" / "nested").mkdir(parents=True)
    (root / "variation").mkdir()
    (root / ".hidden").mkdir()
    shutil.copy(PAIRS / "genome-fhr.fa", root / "genome" / "genome.fa")
    shutil.copy(PAIRS / "genome-plain.fa", root / "genome" / "plain.fa")
    shutil.copy(PAIRS / "annotation-correct.gff3", root / "annotation" / "a.gff3")
    shutil.copy(
        PAIRS / "annotation-no-link.gff3", root / "annotation" / "nested" / "b.gff3"
    )
    shutil.copy(FIXTURES / REFSEQ_GFF3, root / "annotation" / "refseq.gff")
    shutil.copy(FIXTURES / "ncbi-clinvar_vcf_clinvar.vcf", root / "variation" / "c.vcf")
    shutil.copy(FIXTURES / "no-header.fa", root / ".hidden" / "x.fa")
    shutil.copy(FIXTURES / "no-header.fa", root / ".dotfile.fa")
    (root / "pairs.tsv").write_text(
        "# derived\trelated\n"
        "annotation/a.gff3\tgenome/genome.fa\n"
        "annotation/nested/b.gff3\tgenome/plain.fa\n",
        encoding="utf-8",
    )
    return root


def tree(directory):
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def run(release, out, *extra):
    return bioheaders(
        "assess",
        "--recursive",
        "--exclude",
        "pairs.tsv",
        "--output",
        out,
        *extra,
        release,
    )


def test_recursive_walk_mirrors_the_tree_and_skips_hidden_files(release, tmp_path):
    out = tmp_path / "out"
    result = run(release, out)
    assert result.returncode == 0, result.stderr
    written = sorted(tree(out))
    assert written == [
        "annotation/a.gff3.assessment.json",
        "annotation/a.gff3.assessment.md",
        "annotation/nested/b.gff3.assessment.json",
        "annotation/nested/b.gff3.assessment.md",
        "annotation/refseq.gff.assessment.json",
        "annotation/refseq.gff.assessment.md",
        "genome/genome.fa.assessment.json",
        "genome/genome.fa.assessment.md",
        "genome/plain.fa.assessment.json",
        "genome/plain.fa.assessment.md",
        "summary.json",
        "summary.md",
        "summary.tsv",
        "variation/c.vcf.assessment.json",
        "variation/c.vcf.assessment.md",
    ]
    report = json.loads((out / "annotation/refseq.gff.assessment.json").read_text())
    assert report["input"]["path"] == "annotation/refseq.gff"
    stdout = result.stdout.decode()
    assert "annotation/refseq.gff" in stdout
    assert "| Indicator |" in stdout


def test_include_and_exclude_globs(release, tmp_path):
    out = tmp_path / "out"
    result = run(release, out, "--include", "annotation/*", "--exclude", "*/nested/*")
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert [f["path"] for f in summary["files"]] == [
        "annotation/a.gff3",
        "annotation/refseq.gff",
    ]


def test_hidden_files_are_assessed_only_when_included_explicitly(release, tmp_path):
    out = tmp_path / "out"
    result = run(release, out, "--include", ".hidden/*")
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert [f["path"] for f in summary["files"]] == [".hidden/x.fa"]


def test_summary_tsv_columns_and_cells(release, tmp_path):
    out = tmp_path / "out"
    assert run(release, out).returncode == 0
    lines = (out / "summary.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    indicators = [indicator["id"] for indicator in load().indicators]
    assert header == ["path", "format", "scope", "pair_classification"] + indicators
    assert not any("total" in column.lower() for column in header)
    assert len(lines) == 7
    for line in lines[1:]:
        cells = line.split("\t")
        assert len(cells) == len(header)
        assert set(cells[4:]) <= SYMBOLS
    paths = [line.split("\t")[0] for line in lines[1:]]
    assert paths == sorted(paths)
    assert (out / "summary.tsv").read_bytes().endswith(b"\n")
    assert b"\r" not in (out / "summary.tsv").read_bytes()


def test_summary_json_counts_and_no_total(release, tmp_path):
    out = tmp_path / "out"
    assert run(release, out).returncode == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["errors"] == []
    assert summary["root"] == str(release)
    assert len(summary["files"]) == 6
    for entry in summary["files"]:
        assert set(entry) == {
            "path",
            "format",
            "scope",
            "statuses",
            "pair_classification",
        }
        assert len(entry["statuses"]) == 41
    counts = summary["indicator_counts"]
    assert len(counts) == 41
    for indicator, by_status in counts.items():
        assert set(by_status) == set(STATUSES)
        assert sum(by_status.values()) == 6, indicator
    text = json.dumps(summary).lower()
    assert "total" not in text and "score" not in text


def test_pairs_are_verified(release, tmp_path):
    out = tmp_path / "out"
    result = run(release, out, "--pairs", release / "pairs.tsv")
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "summary.json").read_text())
    pairs = {f["path"]: f["pair_classification"] for f in summary["files"]}
    assert pairs["annotation/a.gff3"] == "recorded-match"
    assert pairs["annotation/nested/b.gff3"] == "consistent-unverified"
    assert pairs["annotation/refseq.gff"] is None
    report = json.loads((out / "annotation/a.gff3.assessment.json").read_text())
    assert report["links"][0]["verification"]["related_path"] == "genome/genome.fa"
    tsv = (out / "summary.tsv").read_text(encoding="utf-8")
    assert "annotation/a.gff3\tgff3\tassessed\trecorded-match\t" in tsv


def test_jobs_do_not_change_the_output_and_a_rerun_is_identical(release, tmp_path):
    outputs = []
    for jobs, name in (("1", "one"), ("4", "four"), ("4", "again")):
        out = tmp_path / name
        result = run(release, out, "--pairs", release / "pairs.tsv", "--jobs", jobs)
        assert result.returncode == 0, result.stderr
        outputs.append(tree(out))
    assert outputs[0] == outputs[1] == outputs[2]


def test_rerun_into_the_same_directory_is_byte_identical(release, tmp_path):
    out = release / "reports"  # inside the input tree: must not be assessed
    assert run(release, out).returncode == 0
    first = tree(out)
    assert run(release, out).returncode == 0
    assert tree(out) == first
    summary = json.loads((out / "summary.json").read_text())
    assert not any(f["path"].startswith("reports/") for f in summary["files"])


def test_an_unreadable_file_gives_exit_1_and_the_rest_are_written(release, tmp_path):
    broken = release / "annotation" / "broken.gff3.gz"
    broken.write_bytes(b"\x1f\x8b\x08\x00not really gzip")
    out = tmp_path / "out"
    result = run(release, out)
    assert result.returncode == 1
    assert b"FHR: " in result.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert [e["path"] for e in summary["errors"]] == ["annotation/broken.gff3.gz"]
    assert (out / "annotation/refseq.gff.assessment.json").is_file()
    assert (out / "variation/c.vcf.assessment.json").is_file()
    entry = next(
        f for f in summary["files"] if f["path"] == "annotation/broken.gff3.gz"
    )
    assert entry["scope"] == "error"


def test_several_files_without_recursive(tmp_path):
    out = tmp_path / "out"
    result = bioheaders(
        "assess",
        "--output",
        out,
        FIXTURES / REFSEQ_GFF3,
        FIXTURES / "no-header.fa",
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert sorted(f["path"] for f in summary["files"]) == [
        REFSEQ_GFF3,
        "no-header.fa",
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["--recursive"],  # batch mode without --output
        ["--recursive", "--output", "OUT", "--pairs", "PAIRS", "--related", "GENOME"],
        ["--recursive", "--output", "OUT", "--pairs", "DUPLICATE"],
        ["--output", "OUT"],  # a directory without --recursive
    ],
)
def test_usage_errors_exit_2(release, tmp_path, arguments):
    duplicate = tmp_path / "duplicate.tsv"
    duplicate.write_text(
        "annotation/a.gff3\tgenome/genome.fa\nannotation/a.gff3\tgenome/plain.fa\n",
        encoding="utf-8",
    )
    replace = {
        "OUT": tmp_path / "out",
        "PAIRS": release / "pairs.tsv",
        "GENOME": release / "genome" / "genome.fa",
        "DUPLICATE": duplicate,
    }
    result = bioheaders("assess", *[replace.get(a, a) for a in arguments], release)
    assert result.returncode == 2, result.stderr
    assert not (tmp_path / "out" / "summary.json").exists()


def test_python_api(release, tmp_path):
    out = tmp_path / "api"
    summary = assess_release(
        [release],
        out,
        pairs=release / "pairs.tsv",
        jobs=1,
        exclude=["pairs.tsv"],
    )
    assert (out / "summary.json").is_file()
    assert summary == json.loads((out / "summary.json").read_text())
    with pytest.raises(ValueError):
        assess_release([release], out, pairs=release / "pairs.tsv", related="x")
