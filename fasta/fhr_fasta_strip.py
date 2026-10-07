"""Compatibility wrapper for the installed FHR command."""

from fhr.cli import fasta_strip_main as main

if __name__ == "__main__":
    raise SystemExit(main())
