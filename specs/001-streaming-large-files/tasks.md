# Tasks: Stream FASTA/GFA sequence commands with bounded memory

- [x] T001 Add chunked line scanner `sequence_parts` and `MAX_HEADER_BYTES` in `fhr/__init__.py`; route `header_lines` and `input_fasta`/`input_gfa` through it.
- [x] T002 Add streaming checksum state in `fhr/cli.py`; make `checksum`, `strip_header`, and `combine` feed it.
- [x] T003 Stream the CLI commands: one-pass validate, streamed strip, two-pass combine, scan-only convert.
- [x] T004 Atomic output writes for all commands.
- [x] T005 Tests: chunk sizes 1-7 vs splitlines oracle (LF, CRLF, CR, mixed, no final newline, comments, blank lines, late lines, concatenation, split `\r\n`), header cap, atomic write failure.
- [x] T006 Opt-in memory test (`FHR_MEMORY_TEST=1`) and measurements on a 300 MB FASTA.
- [x] T007 README and CHANGELOG.
