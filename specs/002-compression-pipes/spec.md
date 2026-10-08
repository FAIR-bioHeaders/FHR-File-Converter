# Feature Specification: Compressed FASTA/GFA files and pipes

**Feature Branch**: `feat/compression-pipes`

**Created**: 2026-10-08

**Status**: Draft

**Input**: Assemblies are usually distributed gzip- or BGZF-compressed and
processed in pipelines; the 0.3.2 commands need plain files with known paths.

## Decisions (maintainers' coordinator)

1. Detect gzip by magic bytes (`1f 8b`), not extension; read gzip, multi-member
   gzip, and BGZF with the standard library, streaming, in bounded memory.
2. The FHR checksum covers the decompressed FASTA/GFA bytes, so a file and any
   gzip/BGZF compression of it validate with the same checksum. Plain-file
   behaviour is byte-identical to 0.3.2.
3. Outputs whose path ends in `.gz` or `.bgz` are BGZF, written by a small
   standard-library writer; other outputs and stdout are plain.
4. `-` is stdin or stdout. Combine of stdin spools to a temporary file in
   `TMPDIR`; validate, convert, and strip of stdin are single-pass. Real files keep
   the output-equals-input refusal and atomic writes.
5. Corrupt or truncated gzip input is a concise `FHR:` error with exit status 1.
6. No new runtime dependencies; Python 3.9 compatible.

## User Scenarios & Testing

### User Story 1 - Validate a downloaded compressed assembly (P1)

**Acceptance**: `fhr-fasta-validate genome.fhr.fasta.gz` and
`curl ... | fhr-fasta-validate -` verify the same checksum as the plain file.

### User Story 2 - Combine and strip compressed files (P2)

**Acceptance**: combining to `x.fhr.fasta.gz` writes BGZF that decompresses to the
plain combine output, validates, and strips back to the original payload; htslib
reads it and indexes a stripped BGZF copy for random access.

### User Story 3 - Use the commands in pipelines (P3)

**Acceptance**: validate, strip, combine, and convert read `-` and write `-`, with
`--from`/`--to` naming metadata formats for standard streams.

### Edge Cases

- Gzip data in a file without a `.gz` extension; plain data in a `.gz` file.
- Multi-member gzip and the empty BGZF end-of-file block.
- Truncated data, corrupt deflate data, CRC mismatch, trailing garbage.
- Strip from stdin to stdout cannot pre-scan; an error can follow partial output.
- `samtools faidx` rejects FASTA containing `;` lines, compressed or not.

## Requirements

- **FR-001**: Checksums and outputs for plain files are unchanged from 0.3.2.
- **FR-002**: Compressed input checksums equal those of the decompressed bytes.
- **FR-003**: BGZF blocks hold at most 65280 uncompressed bytes, carry the `BC`
  extra subfield with BSIZE, and end with the standard 28-byte EOF block.
- **FR-004**: Memory stays bounded for compressed input and standard streams.

## Success Criteria

- **SC-001**: Peak RSS below 256 MB for a 300 MB gzip FASTA in every command,
  including stdin (opt-in `FHR_MEMORY_TEST=1`).
- **SC-002**: All existing tests pass unchanged on Python 3.9 and 3.13.
