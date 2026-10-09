# FAIR-bioHeaders Tools

[![Tests](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/actions/workflows/pytest.yaml)
[![Specification DOI](https://img.shields.io/badge/Specification_DOI-10.5281%2Fzenodo.6762549-blue)](https://doi.org/10.5281/zenodo.6762549)
[![File Converter DOI](https://img.shields.io/badge/File_Converter_DOI-10.5281%2Fzenodo.6762547-blue)](https://doi.org/10.5281/zenodo.6762547)

Convert and validate FAIR-bioHeaders Reference genome (FHR) metadata in JSON,
YAML, FASTA, GFA, and HTML microdata. See
[FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification) for the
schema and metadata design. This is the `fair-bioheaders` package, version
**0.4.0**, formerly the FHR File Converter (`fhr`); see
[Renamed from fhr](#renamed-from-fhr).

## Install

For a published release:

```bash
python -m pip install fair-bioheaders
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
bioheaders convert examples/example.fhr.yaml /tmp/example.fhr.json
bioheaders validate /tmp/example.fhr.json
bioheaders combine examples/example.fhr.yaml genome.fasta -o genome.fhr.fasta
bioheaders verify genome.fhr.fasta
bioheaders strip genome.fhr.fasta genome.stripped.fasta
bioheaders combine examples/example.fhr.yaml assembly.gfa -o assembly.fhr.gfa
bioheaders verify assembly.fhr.gfa
bioheaders strip assembly.fhr.gfa assembly.stripped.gfa
```

`combine`, `strip`, and `verify` (also called `checksum`) take the FASTA or GFA
type from the sequence file's extension, ignoring `.gz` or `.bgz`; give
`--type fasta` or `--type gfa` for stdin or other extensions. `bioheaders
--version` prints the version and `bioheaders COMMAND --help` describes each
command. The original commands remain available with the same options and output:

| `bioheaders` command | Original command |
| --- | --- |
| `convert INPUT OUTPUT` | `fhr-convert` |
| `validate INPUT` | `fhr-validate` |
| `combine METADATA SEQUENCE` | `fhr-fasta-combine`, `fhr-gfa-combine` |
| `strip INPUT [OUTPUT]` | `fhr-fasta-strip`, `fhr-gfa-strip` |
| `verify INPUT` | `fhr-fasta-validate`, `fhr-gfa-validate` |

`convert INPUT OUTPUT` detects `.json`, `.yaml`/`.yml`, `.fasta`/`.fa`/`.fna`,
`.gfa`, and `.html` from extensions. It validates metadata before writing output;
FASTA/GFA output contains a metadata header only. To include sequence data, use
`combine METADATA SEQUENCE [-o OUTPUT]`, whose default output is `SEQUENCE.fhr.fasta`
or `SEQUENCE.fhr.gfa` with the last extension replaced. Existing FHR header lines
are replaced. Inputs are not overwritten by sequence helpers.

`strip INPUT [OUTPUT]` writes to stdout if OUTPUT is omitted. Only FHR-prefixed
lines are removed; other bytes, including ordinary comments and CRLF endings,
are preserved. `validate` checks metadata, while `verify` (`fhr-fasta-validate`,
`fhr-gfa-validate`) also verifies the exact-byte file checksum. Failures exit
with status 1.

FASTA/GFA commands stream their input in 1 MiB chunks, so memory use does not grow
with file size (about 35 MB peak for a 1 GB FASTA). Validate reads the file once;
combine reads it twice. FHR header lines are limited to 16 MiB in total. Outputs
are written to a temporary file in the destination directory and then renamed,
so a failed command leaves no partial output.

### Compressed files and pipes

```bash
bioheaders combine examples/example.fhr.yaml genome.fa.gz    # writes genome.fhr.fasta.gz
bioheaders verify genome.fhr.fasta.gz
bioheaders strip genome.fhr.fasta.gz genome.stripped.fa.gz
zcat genome.fa.gz | bioheaders combine --type fasta examples/example.fhr.yaml - > genome.fhr.fasta
curl -sL https://example.org/genome.fhr.fasta.gz | bioheaders verify --type fasta -
bioheaders convert genome.fhr.fasta.gz - --to json
bioheaders convert - metadata.yaml --from json < metadata.json
```

Gzip input, including multi-member gzip and BGZF, is recognized by its magic
bytes rather than its extension and decompressed as it streams. The checksum
covers the decompressed FASTA/GFA bytes, so `genome.fa` and any gzip or BGZF
compression of it have the same checksum. A corrupt or truncated gzip file is an
error. Formats are taken from the extension before `.gz` or `.bgz`.

Outputs whose path ends in `.gz` or `.bgz` are written as BGZF, which `gzip`,
`zcat`, `bgzip`, and htslib read. A combine without `-o` keeps the input's
compression extension. Other outputs, and stdout, are never compressed. Note that
`samtools faidx` rejects FASTA files containing `;` lines, compressed or not, so
index a stripped copy for random access.

`-` reads stdin or writes stdout: the input of verify, strip, combine (the
sequence), convert, and validate, and the output of strip, convert, and
`combine -o`. Combine of stdin writes stdout by default. Convert and validate
need `--from FORMAT` for stdin and convert needs `--to FORMAT` for stdout
(`json`, `yaml`, `fasta`, `gfa`, or `html`); the `bioheaders` sequence commands
need `--type` for stdin. Stdin is read
once: combine spools the stripped sequence to a temporary file in `TMPDIR` (as
large as the sequence) while hashing it. Strip from stdin to stdout writes as it
reads, so an error late in the input can follow partial output; check the exit
status. Strip of a file to stdout still checks the whole file before writing.

## Python

```python
from bioheaders import fhr

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
`bioheaders.cli` holds the command implementations and the byte-level helpers
(`checksum`, `combine`, `strip_header`, `open_input`, `write_to`, and others).

## Renamed from fhr

In 0.4.0 the PyPI package `fhr` was renamed `fair-bioheaders`, the Python package
`fhr` was renamed `bioheaders`, and the repository moved from FHR-File-Converter
to [FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)
(old links redirect). The new names leave room for other FAIR-bioHeaders header
types. Nothing that worked with 0.3 stops working:

- The eight `fhr-*` commands are unchanged and print no deprecation notices, so
  scripts and pipelines that read their output or stderr keep working. They are
  not deprecated, but new scripts can use `bioheaders`.
- `import fhr`, `from fhr import fhr`, and `from fhr.cli import ...` still work:
  `fhr` and `fhr.cli` are the same module objects as `bioheaders` and
  `bioheaders.cli`. Importing `fhr` emits one `DeprecationWarning`; replace
  `fhr` with `bioheaders` in imports. The `fhr` metadata class keeps its name.
- `pip install fhr` installs `fhr` 0.4.0, a compatibility package without code
  that requires the same version of `fair-bioheaders`, so existing requirements
  and `pip install -U fhr` keep working. Prefer `fair-bioheaders` in new
  requirements. The compatibility package also installs the `fhr-*` commands, so
  if you uninstall `fhr` 0.4 later, restore them with
  `python -m pip install --force-reinstall --no-deps fair-bioheaders`.
- In an environment that still has `fhr` 0.3, run `python -m pip uninstall fhr`
  before `python -m pip install fair-bioheaders` (or upgrade with
  `python -m pip install -U fhr`); otherwise the old `fhr` package files shadow
  the new compatibility module.
- Citations and Zenodo DOIs are unchanged.

Checksum helpers require SHA-512/256 support in the Python build. Some Apple
system Python builds omit it; use an OpenSSL-enabled Python distribution.
Metadata conversion and validation do not require that hash implementation.

## v0.3 compatibility and identity

- Required fields and `schemaVersion: 1` remain unchanged since v0.3.0.
- `assemblySoftware` accepts a legacy string or optional structured software
  objects with name, URI, version, and command options. `assemblyProtocol` is a URI.
- `vitalStats.N90` is base pairs; `vitalStats.gcContent` is 0–100 percent.
- Optional `seqcol_id` stores a supplied 32-character base64url top-level refget
  digest. The converter preserves it; it does not compute or verify SeqCol identity.
- Checksums use base64 SHA-512/256 of all original file bytes except the one scalar
  checksum header line, including its newline. Metadata is covered. MD5 hex and
  payload-only checksums from old examples are not valid v0.3 checksums; recombine
  metadata with the original sequence file to calculate the new value.
- The checksum value must be a single-line scalar on the checksum line. Header
  lines must be UTF-8 and must not contain U+0085, U+2028, or U+2029. FASTA/GFA
  files must not begin with a UTF-8 byte order mark. Other sequence bytes may use
  any encoding.
- Metadata must be JSON-compatible: duplicate keys, YAML anchors, aliases, and
  merge keys are rejected.
- `;~`/`#~` lines must form the leading header block, before the first FASTA `>`
  line or the first GFA record line; ordinary comments and blank lines may be
  mixed in. A `;~`/`#~` line after sequence data, including a concatenated
  second file, is an error.
- HTML exports use FHR item scopes and `data-fhr-type` annotations for lossless
  arrays, numbers, objects, and strings. External microdata must represent nested
  items properly; incomplete legacy markup may need regeneration.
- Incomplete constructors now emit missing fields rather than empty defaults.
  Validate after loading to obtain actionable schema errors. Obsolete positional
  constructor arguments should be converted to keywords.

See the [format reference](https://github.com/FAIR-bioHeaders/FHR-Specification/blob/main/docs/FORMAT.md)
and [release notes](CHANGELOG.md). JSON/YAML/HTML example identifiers are synthetic.
The FASTA/GFA fixtures contain verified FHR checksums; their SeqCol IDs are placeholders.

## Docker

```bash
docker build -t fair-bioheaders-tools .
docker run --rm fair-bioheaders-tools --help
```

The image runs `fhr-convert`; use `--entrypoint bioheaders` for the other
commands. Mount inputs/outputs into the container for conversion. See
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

## Licensing

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

New project contributions from March 2025 onward use [MPL-2.0](LICENSE). David Molik left USDA in February 2025. Historical USDA public-domain material remains public domain within the United States; its original notice is preserved in LICENSE. Previously granted permissions and third-party terms remain intact. The project includes both historical material and subsequent MPL-2.0 contributions; file notices and history identify provenance.
