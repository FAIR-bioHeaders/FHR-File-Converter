# Changelog

## 0.3.0 — unreleased (coordinated FHR v0.3, from v0.2)

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
