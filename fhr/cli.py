"""Shared command implementations for FHR metadata and sequence files."""

import argparse
import base64
import hashlib
import os
import re
import stat
import sys
import tempfile
from copy import deepcopy
from itertools import chain
from pathlib import Path

import yaml
from jsonschema.exceptions import ValidationError

from . import (
    DATA,
    END,
    HEADER,
    __version__,
    fhr,
    header_text,
    load_yaml,
    read_chunks,
    sequence_parts,
)

FORMATS = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".fa": "fasta",
    ".fasta": "fasta",
    ".fna": "fasta",
    ".gfa": "gfa",
    ".html": "microdata",
}


def file_format(path):
    try:
        return FORMATS[Path(path).suffix.lower()]
    except KeyError:
        raise ValueError(f"Unsupported file extension: {path}") from None


def read_metadata(path, content=None):
    data = fhr()
    if content is None:
        with Path(path).open("rb") as stream:
            getattr(data, "input_" + file_format(path))(stream)
    else:
        getattr(data, "input_" + file_format(path))(content)
    return data


def write_metadata(data, path):
    content = getattr(data, "output_" + file_format(path))()
    write_output(path, lambda output: output.write(content), "w", encoding="utf-8")


def write_output(path, write, mode="wb", **options):
    """Call ``write`` with a file object, then atomically replace ``path``.

    A temporary file in the destination directory receives the output and only
    replaces the destination once ``write`` has succeeded, so a failure never
    leaves partial output. Existing non-regular files such as ``/dev/null`` are
    written directly.
    """
    target = os.path.realpath(path)
    try:
        status = os.stat(target)
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        permissions = 0o666 & ~umask
    else:
        if not stat.S_ISREG(status.st_mode):
            with open(path, mode, **options) as output:
                write(output)
            return
        permissions = stat.S_IMODE(status.st_mode)
    directory, name = os.path.split(target)
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{name}.", suffix=".tmp", dir=directory
        )
    except OSError as error:
        # Report the requested path, as a direct write would.
        raise type(error)(error.errno, error.strerror, os.fspath(path)) from None
    try:
        with os.fdopen(descriptor, mode, **options) as output:
            os.chmod(temporary, permissions)
            write(output)
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _output_is_input(output, inputs):
    output = Path(output)
    inputs = [Path(path) for path in inputs]
    if any(output.resolve() == path.resolve() for path in inputs):
        return True
    return output.exists() and any(
        output.samefile(path) for path in inputs if path.exists()
    )


def _prefix(kind):
    return b";~" if kind == "fasta" else b"#~"


def strip_parts(chunks, kind):
    """Yield the bytes of FASTA/GFA chunks except FHR header lines."""
    for part, data in sequence_parts(chunks, _prefix(kind)):
        if part is DATA:
            yield data


def _stripped(path, kind):
    with Path(path).open("rb") as stream:
        yield from strip_parts(read_chunks(stream), kind)


def _drain(parts):
    for _ in parts:
        pass


def strip_header(content, kind):
    return b"".join(strip_parts(read_chunks(content), kind))


class SequenceScan:
    """FHR header lines and checksum state of FASTA/GFA bytes read in one pass.

    Every byte is hashed as it streams except the scalar checksum line: the root
    indentation of header lines can only decrease as lines arrive, so at most one
    candidate checksum line stays valid, and a digest copied before it excludes it.
    """

    def __init__(self, chunks, kind):
        self.prefix = _prefix(kind)
        self.pattern = re.compile(
            b"^" + re.escape(self.prefix) + rb"[ \t]*checksum[ \t]*:"
        )
        self.header = []
        self.root_indent = None
        self.matches = 0
        self.checksum_line = None
        self.excluded = None
        try:
            self.digest = hashlib.new("sha512_256")
        except ValueError:
            self.digest = None
        self.hash_available = self.digest is not None
        for part, data in sequence_parts(chunks, self.prefix):
            if part is HEADER:
                self._header_line(data)
            elif part is END:
                # No more header lines: keep only the digest that can be used.
                self.digest = None
                if self.matches != 1:
                    self.excluded = None
            else:
                self._update(data)

    def _update(self, data):
        if self.digest is not None:
            self.digest.update(data)
        if self.excluded is not None:
            self.excluded.update(data)

    def _header_line(self, line):
        self.header.append(line)
        metadata = line[len(self.prefix) :]
        if (
            metadata.strip()
            and not metadata.lstrip().startswith(b"#")
            and not re.match(
                rb"^(?:%|---(?:[ \t]|$)|\.\.\.(?:[ \t]|$))",
                metadata.lstrip(b" \t"),
            )
        ):
            indent = len(metadata) - len(metadata.lstrip(b" \t"))
            if self.root_indent is None or indent < self.root_indent:
                self.root_indent = indent
                self.matches = 0
                self.excluded = None
            if indent == self.root_indent and self.pattern.match(line):
                self.matches += 1
                self.checksum_line = line
                self.excluded = None
                if self.matches == 1 and self.digest is not None:
                    self.excluded = self.digest.copy()
                if self.digest is not None:
                    self.digest.update(line)
                return
        self._update(line)

    def checksum(self):
        """Return the FHR checksum after checking the checksum header line."""
        if self.matches != 1:
            raise ValueError("Expected exactly one scalar checksum header line")
        prefix = self.prefix
        # Decode and parse exactly as input_fasta/input_gfa would.
        header = load_yaml("\n".join(header_text(line, prefix) for line in self.header))
        # The excluded line must hold the whole value; continuation lines are hashed.
        try:
            value = load_yaml(header_text(self.checksum_line, prefix))
        except yaml.YAMLError:
            value = None
        if not (
            isinstance(value, dict)
            and list(value) == ["checksum"]
            and isinstance(value["checksum"], str)
            and value["checksum"]
            and isinstance(header, dict)
            and header.get("checksum") == value["checksum"]
        ):
            raise ValueError(
                "The checksum header line must contain the complete checksum value "
                "as a single-line scalar"
            )
        if not self.hash_available:
            raise ValueError(
                "SHA-512/256 is unavailable in this Python build; "
                "use a Python distribution with OpenSSL support"
            )
        return base64.b64encode(self.excluded.digest()).decode("ascii")


def checksum(content, kind):
    """Hash all original bytes except the one scalar checksum metadata line."""
    return SequenceScan(read_chunks(content), kind).checksum()


def combined_header(data, body, kind):
    """Return the header that combines ``data`` with stripped ``body`` chunks."""
    data = fhr(**deepcopy(data.__dict__))
    data.checksum = "A" * 43 + "="
    preliminary = getattr(data, "output_" + kind)().encode("utf-8")
    data.checksum = SequenceScan(chain([preliminary], body), kind).checksum()
    data.fhr_validate()
    return getattr(data, "output_" + kind)().encode("utf-8")


def combine(data, content, kind):
    body = strip_header(content, kind)
    return combined_header(data, read_chunks(body), kind) + body


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--version", action="version", version=__version__)
    return result


def run(action):
    try:
        return action() or 0
    except ValidationError as error:
        print(
            f"FHR: schema validation failed at {error.json_path}: {error.message}",
            file=sys.stderr,
        )
        return 1
    except RecursionError:
        print("FHR: metadata is nested too deeply", file=sys.stderr)
        return 1
    except (
        OSError,
        ValueError,
        TypeError,
        AttributeError,
        yaml.YAMLError,
    ) as error:
        print(f"FHR: {error}", file=sys.stderr)
        return 1


def convert_main():
    def action():
        args_parser = parser(
            "Convert FHR metadata between JSON, YAML, FASTA, GFA, and HTML"
        )
        args_parser.add_argument("input")
        args_parser.add_argument("output")
        args = args_parser.parse_args()
        if _output_is_input(args.output, [args.input]):
            raise ValueError("Output must differ from the input file")
        data = read_metadata(args.input)
        data.fhr_validate()
        write_metadata(data, args.output)

    return run(action)


def validate_main():
    def action():
        args_parser = parser("Validate FHR metadata against the bundled schema")
        args_parser.add_argument("input")
        args = args_parser.parse_args()
        read_metadata(args.input).fhr_validate()
        print("FHR metadata is valid.")

    return run(action)


def combine_main(kind):
    def action():
        args_parser = parser(
            f"Combine metadata with {kind.upper()} and calculate its FHR checksum"
        )
        args_parser.add_argument("metadata")
        args_parser.add_argument("sequence")
        args_parser.add_argument("-o", "--output")
        args = args_parser.parse_args()
        if file_format(args.sequence) != kind:
            raise ValueError(f"Expected a {kind.upper()} sequence file")
        output = args.output or str(Path(args.sequence).with_suffix(f".fhr.{kind}"))
        if _output_is_input(output, [args.sequence, args.metadata]):
            raise ValueError("Output must differ from the input files")
        data = read_metadata(args.metadata)
        # Hash the stripped sequence, then read it again to write it.
        header = combined_header(data, _stripped(args.sequence, kind), kind)

        def write(output):
            output.write(header)
            output.writelines(_stripped(args.sequence, kind))

        write_output(output, write)

    return run(action)


def strip_main(kind):
    def action():
        args_parser = parser(
            f"Strip FHR metadata from {kind.upper()} without changing other bytes"
        )
        args_parser.add_argument("input")
        args_parser.add_argument("output", nargs="?")
        args = args_parser.parse_args()
        if file_format(args.input) != kind:
            raise ValueError(f"Expected a {kind.upper()} file")
        if args.output:
            if _output_is_input(args.output, [args.input]):
                _drain(_stripped(args.input, kind))  # Report input errors first.
                raise ValueError("Output must differ from the input file")
            write_output(
                args.output,
                lambda output: output.writelines(_stripped(args.input, kind)),
            )
        else:
            # Find input errors before writing anything to stdout.
            _drain(_stripped(args.input, kind))
            sys.stdout.buffer.writelines(_stripped(args.input, kind))

    return run(action)


def checksum_main(kind):
    def action():
        args_parser = parser(f"Validate {kind.upper()} metadata and its FHR checksum")
        args_parser.add_argument("input")
        args = args_parser.parse_args()
        if file_format(args.input) != kind:
            raise ValueError(f"Expected a {kind.upper()} file")
        with Path(args.input).open("rb") as stream:
            scan = SequenceScan(read_chunks(stream), kind)
        data = fhr()
        data._input_header_lines(scan.header, scan.prefix)
        data.fhr_validate()
        if data.checksum != scan.checksum():
            raise ValueError("Checksum verification failed")
        print("Checksum verified.")

    return run(action)


def fasta_combine_main():
    return combine_main("fasta")


def fasta_strip_main():
    return strip_main("fasta")


def fasta_validate_main():
    return checksum_main("fasta")


def gfa_combine_main():
    return combine_main("gfa")


def gfa_strip_main():
    return strip_main("gfa")


def gfa_validate_main():
    return checksum_main("gfa")
