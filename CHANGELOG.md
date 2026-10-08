# Changelog

## 0.3.1 — unreleased (patch release of v0.3)

- Reject duplicate mapping keys in FASTA/GFA headers, YAML, and JSON; a later
  `;~`/`#~` line can no longer silently override an earlier header field.
- Reject YAML anchors, aliases, and merge keys (unbounded alias expansion and
  YAML 1.1-only merge semantics).
- Parse FASTA/GFA headers from the same byte lines that are hashed; only header
  lines must be UTF-8. Header lines must not contain U+0085, U+2028, or U+2029,
  which YAML reads as line breaks; the YAML writer escapes them.
- Require the checksum value on the checksum line itself as a single-line scalar.
- Require FHR lines to form the leading header block; reject `;~`/`#~` lines
  after the first FASTA `>` line or GFA record line, including concatenated files.
- Reject FASTA/GFA files that begin with a UTF-8 byte order mark; ignore one at
  the start of JSON, YAML, or HTML metadata.
- Read microdata with HTML implied end tags, whitespace-separated `itemtype` and
  `itemprop` lists, first-wins duplicate attributes, and microdata value attributes
  only on their defining elements. Typed values must match `data-fhr-type`.
- Report schema errors as a JSON path and message; report excessive nesting as an error.
- Development dependencies: pytest 9.0.3+ on Python 3.10+ (CVE-2025-71176) and
  black 24.3.0+ on Python 3.9 (CVE-2024-21503). pytest 9 does not support 3.9.

## 0.3.0 — 2026-10-07 (coordinated FHR v0.3, from v0.2)

- Package metadata moves from the checkout's historical 0.1.1 to the coordinated 0.3.0 target.
- Package the schema and CLI entry points so installed tools work outside the checkout.
- Replace inconsistent format-specific state with a preserved metadata mapping;
  input methods accept text, bytes, or readable streams. Optional fields are not filled with null.
- Validate parsed objects with date/URI format checking. Add assembly provenance,
  protocol, N90/GC, and supplied SeqCol support; preserve legacy software strings.
- Repair YAML output, FASTA/GFA combine and strip inputs, and failure exit codes.
- Preserve non-FHR sequence bytes and comments. Verify exact-byte SHA-512/256 over
  metadata plus sequence, excluding the checksum line. Regenerate old MD5/payload-only checksums.
- Serialize YAML headers safely and HTML with escaped values and explicit types.
- Add regression/installed CLI tests, update CI, guidance, examples, Docker, and Chicago citations.

Constructor keyword fields remain available; obsolete positional arguments need
migration to keywords. Empty optional defaults are no longer emitted. SeqCol
identifiers are preserved, not calculated or checked against sequence contents.
Sequence helpers currently read complete files into memory.
