# FHR File Converter

[![Converter tests](https://github.com/FAIR-bioHeaders/FHR-File-Converter/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/FAIR-bioHeaders/FHR-File-Converter/actions/workflows/pytest.yaml)
[![Specification DOI](https://img.shields.io/badge/Specification_DOI-10.5281%2Fzenodo.6762549-blue)](https://doi.org/10.5281/zenodo.6762549)
[![File Converter DOI](https://img.shields.io/badge/File_Converter_DOI-10.5281%2Fzenodo.6762547-blue)](https://doi.org/10.5281/zenodo.6762547)

Convert and validate FHR genome metadata in JSON, YAML, FASTA, GFA, and HTML
microdata. See [FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification)
for the schema and metadata design. The v0.3 release is version **0.3.0**.

## Install

For a published release:

```bash
python -m pip install fhr
```

For this checkout and its development checks (Python 3.9 or later):

```bash
python -m pip install poetry
poetry install
poetry run pytest
poetry run ruff check .
poetry run isort . --check-only
poetry run black . --check
```

## Commands

```bash
fhr-convert examples/example.fhr.yaml /tmp/example.fhr.json
fhr-validate /tmp/example.fhr.json
fhr-fasta-combine examples/example.fhr.yaml genome.fasta -o genome.fhr.fasta
fhr-fasta-validate genome.fhr.fasta
fhr-fasta-strip genome.fhr.fasta genome.stripped.fasta
fhr-gfa-combine examples/example.fhr.yaml assembly.gfa -o assembly.fhr.gfa
fhr-gfa-validate assembly.fhr.gfa
fhr-gfa-strip assembly.fhr.gfa assembly.stripped.gfa
```

`fhr-convert INPUT OUTPUT` detects `.json`, `.yaml`/`.yml`, `.fasta`/`.fa`/`.fna`,
`.gfa`, and `.html` from extensions. It validates metadata before writing output;
FASTA/GFA output contains a metadata header only. To include sequence data, use
`combine METADATA SEQUENCE [-o OUTPUT]`, whose default output is `SEQUENCE.fhr.fasta`
or `SEQUENCE.fhr.gfa` with the last extension replaced. Existing FHR header lines
are replaced. Inputs are not overwritten by sequence helpers.

`strip INPUT [OUTPUT]` writes to stdout if OUTPUT is omitted. Only FHR-prefixed
lines are removed; other bytes, including ordinary comments and CRLF endings,
are preserved. `fhr-validate` checks metadata, while FASTA/GFA validate commands
also verify the exact-byte file checksum. Failures exit with status 1.

## Python

```python
from fhr import fhr

metadata = fhr()
with open("examples/example.fhr.yaml", encoding="utf-8") as stream:
    metadata.input_yaml(stream)
metadata.fhr_validate()
print(metadata.output_json())
```

Input methods accept text, UTF-8 bytes, or readable streams. Optional fields stay
absent until supplied. The mapping is preserved across supported format round
trips; HTML values are escaped and explicitly typed. Keywords can initialize an
instance (`fhr(genome="example")`), and fields remain accessible as attributes.
The installed schema is loaded from package resources rather than the working
directory, so commands work outside the checkout. No schema is downloaded at runtime.

Checksum helpers require SHA-512/256 support in the Python build. Some Apple
system Python builds omit it; use an OpenSSL-enabled Python distribution.
Metadata conversion and validation do not require that hash implementation.

## v0.3 compatibility and identity

- Required fields and `schemaVersion: 1` remain unchanged; the package is 0.3.0.
- `assemblySoftware` accepts a legacy string or optional structured software
  objects with name, URI, version, and command options. `assemblyProtocol` is a URI.
- `vitalStats.N90` is base pairs; `vitalStats.gcContent` is 0–100 percent.
- Optional `seqcol_id` stores a supplied 32-character base64url top-level refget
  digest. The converter preserves it; it does not compute or verify SeqCol identity.
- Checksums use base64 SHA-512/256 of all original file bytes except the one scalar
  checksum header line, including its newline. Metadata is covered. MD5 hex and
  payload-only checksums from old examples are not valid v0.3 checksums; recombine
  metadata with the original sequence file to calculate the new value.
- HTML exports use FHR item scopes and `data-fhr-type` annotations for lossless
  arrays, numbers, objects, and strings. External microdata must represent nested
  items properly; incomplete legacy markup may need regeneration.
- Incomplete constructors now emit missing fields rather than empty defaults.
  Validate after loading to obtain actionable schema errors. Obsolete positional
  constructor arguments should be converted to keywords.

See the [format reference](https://github.com/FAIR-bioHeaders/FHR-Specification/blob/main/docs/FORMAT.md)
and [release notes](CHANGELOG.md). JSON/YAML/HTML example identifiers are synthetic.
The FASTA/GFA fixtures contain verified FHR checksums; their SeqCol IDs are placeholders.
Sequence helpers currently read the file into memory; stream processing is future work.

## Docker

```bash
docker build -t fhr-file-converter .
docker run --rm fhr-file-converter --help
```

Mount inputs/outputs into the container for conversion. See
[CONTRIBUTING](CONTRIBUTING.md), [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md),
[SECURITY](SECURITY.md), and [AGENTS](AGENTS.md) for project guidance.

## Citing FHR

Chicago bibliography entries are used below. Cite the published paper for a
general description of FHR; cite the specification or converter when using that
resource directly. The software and specification links are concept DOIs; for a
specific release, use the corresponding version DOI from Zenodo. Authors and
years follow the records resolved by the concept DOIs at the v0.3 documentation
update, and can change as later records are published.

### Published paper

Wright, Adam, Mark D. Wilkinson, Christopher Mungall, Scott Cain, Stephen Richards, Paul Sternberg, Ellen Provin, Jonathan L. Jacobs, Scott Geib, Daniela Raciti, Karen Yook, Lincoln Stein, and David C. Molik. “FAIR Header Reference Genome: A TRUSTworthy Standard.” *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122. https://doi.org/10.1093/bib/bbae122.

### Specification

Molik, David. *FHR Specification*. Data set. 2022. https://doi.org/10.5281/zenodo.6762549.

### Converter

Molik, David, and Adam Wright. *FHR File Converter*. Computer software. 2024. https://doi.org/10.5281/zenodo.6762547.

Machine-readable entries are maintained in
[FHR-Citation](https://github.com/FAIR-bioHeaders/FHR-Citation/blob/main/citation.bib).
