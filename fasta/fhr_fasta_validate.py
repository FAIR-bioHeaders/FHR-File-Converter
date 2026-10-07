"""Compatibility wrapper for the installed FHR command."""

from fhr.cli import fasta_validate_main as main

if __name__ == "__main__":
    raise SystemExit(main())
