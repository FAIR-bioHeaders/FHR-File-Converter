import argparse
import os
import sys
import textwrap

from fhr import fhr


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Validate a FHR metadata file",
        epilog=textwrap.dedent(
            """\
                    positional <file> input and output files
                        input files can be one of:
                            <input>.yml
                            <input>.fasta  - fasta contining a fhr header
                            <input>.html   - html containing microdata
                            <input>.json   - json containing fhr header
                            <input>.gfa    - gfa containing a fhr header

                            second input must be a gfa file
                            """
        ),
    )

    parser.add_argument(
        "file", nargs=2, metavar="<file>", help="input followed by gfa output"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.0.1")

    args = parser.parse_args()

    fhr_to_be_combined = fhr()

    input_filepath = args.file[0]

    with open(input_filepath, "r") as input_file:
        if input_filepath.endswith(".yml") or input_filepath.endswith(".yaml"):
            fhr_to_be_combined.input_yaml(input_file)
        elif input_filepath.endswith(".fasta") or input_filepath.endswith(".fa"):
            fhr_to_be_combined.input_fasta(input_file)
        elif input_filepath.endswith(".json"):
            fhr_to_be_combined.input_json(input_file)
        elif input_filepath.endswith(".html"):
            fhr_to_be_combined.input_microdata(input_file)
        elif input_filepath.endswith(".gfa"):
            fhr_to_be_combined.input_gfa(input_file)
        else:
            sys.exit("Input file extention not found")

    output_filename = os.path.splitext(args.file[1])[0] + ".fhr.gfa"

    with open(input_filepath, "r") as sources:
        gfa_lines = sources.readlines()

    with open(output_filename, "w") as output_file:
        output_content = fhr_to_be_combined.output_gfa()
        output_file.write(output_content)
        for line in gfa_lines:
            output_file.write(line)
