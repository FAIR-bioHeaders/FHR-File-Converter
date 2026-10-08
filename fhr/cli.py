"""Shared command implementations for FHR metadata and sequence files."""

import argparse
import base64
import hashlib
import re
import sys
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema.exceptions import ValidationError

from . import __version__, fhr, header_lines, header_text, load_yaml, split_lines

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
        content = Path(path).read_bytes()
    getattr(data, "input_" + file_format(path))(content)
    return data


def write_metadata(data, path):
    Path(path).write_text(
        getattr(data, "output_" + file_format(path))(), encoding="utf-8"
    )


def _output_is_input(output, inputs):
    output = Path(output)
    inputs = [Path(path) for path in inputs]
    if any(output.resolve() == path.resolve() for path in inputs):
        return True
    return output.exists() and any(
        output.samefile(path) for path in inputs if path.exists()
    )


def strip_header(content, kind):
    prefix = b";~" if kind == "fasta" else b"#~"
    lines = split_lines(content)
    header_lines(lines, prefix)
    return b"".join(line for line in lines if not line.startswith(prefix))


def checksum(content, kind):
    """Hash all original bytes except the one scalar checksum metadata line."""
    prefix = b";~" if kind == "fasta" else b"#~"
    pattern = re.compile(b"^" + re.escape(prefix) + rb"[ \t]*checksum[ \t]*:")
    lines = split_lines(content)
    metadata_lines = header_lines(lines, prefix)
    metadata = [line[len(prefix) :] for line in metadata_lines]
    meaningful = [
        line
        for line in metadata
        if line.strip()
        and not line.lstrip().startswith(b"#")
        and not re.match(
            rb"^(?:%|---(?:[ \t]|$)|\.\.\.(?:[ \t]|$))", line.lstrip(b" \t")
        )
    ]
    root_indent = min(
        (len(line) - len(line.lstrip(b" \t")) for line in meaningful), default=0
    )

    def is_checksum(line):
        if not pattern.match(line):
            return False
        yaml_line = line[len(prefix) :]
        return len(yaml_line) - len(yaml_line.lstrip(b" \t")) == root_indent

    matches = [line for line in lines if is_checksum(line)]
    if len(matches) != 1:
        raise ValueError("Expected exactly one scalar checksum header line")
    # Decode and parse exactly as input_fasta/input_gfa would.
    header = load_yaml("\n".join(header_text(line, prefix) for line in metadata_lines))
    # The excluded line must hold the whole value; continuation lines are hashed.
    try:
        value = load_yaml(header_text(matches[0], prefix))
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
    try:
        digest = hashlib.new("sha512_256")
    except ValueError:
        raise ValueError(
            "SHA-512/256 is unavailable in this Python build; "
            "use a Python distribution with OpenSSL support"
        ) from None
    for line in lines:
        if not is_checksum(line):
            digest.update(line)
    return base64.b64encode(digest.digest()).decode("ascii")


def combine(data, content, kind):
    data = fhr(**deepcopy(data.__dict__))
    data.checksum = "A" * 43 + "="
    body = strip_header(content, kind)
    preliminary = getattr(data, "output_" + kind)().encode("utf-8") + body
    data.checksum = checksum(preliminary, kind)
    data.fhr_validate()
    return getattr(data, "output_" + kind)().encode("utf-8") + body


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
        content = combine(
            read_metadata(args.metadata), Path(args.sequence).read_bytes(), kind
        )
        Path(output).write_bytes(content)

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
        content = strip_header(Path(args.input).read_bytes(), kind)
        if args.output:
            if _output_is_input(args.output, [args.input]):
                raise ValueError("Output must differ from the input file")
            Path(args.output).write_bytes(content)
        else:
            sys.stdout.buffer.write(content)

    return run(action)


def checksum_main(kind):
    def action():
        args_parser = parser(f"Validate {kind.upper()} metadata and its FHR checksum")
        args_parser.add_argument("input")
        args = args_parser.parse_args()
        if file_format(args.input) != kind:
            raise ValueError(f"Expected a {kind.upper()} file")
        content = Path(args.input).read_bytes()
        data = read_metadata(args.input, content)
        data.fhr_validate()
        if data.checksum != checksum(content, kind):
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
