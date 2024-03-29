import argparse
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
                            <input>.json   - json containing a fhr header
                            <input>.gfa    - gfa file contining a fhr header
                            """
        ),
    )

    parser.add_argument(
        "file", nargs=1, metavar="<file>", help="input followed by output"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.0.1")

    args = parser.parse_args()

    fhr_to_be_validated = fhr()

    with open(args.file[0], "r") as input_file:
        if args.file[0].endswith(".yml") or args.file[0].endswith(".yaml"):
            fhr_to_be_validated.input_yaml(input_file)
        elif args.file[0].endswith(".fasta") or args.file[0].endswith(".fa"):
            fhr_to_be_validated.input_fasta(input_file)
        elif args.file[0].endswith(".json"):
            fhr_to_be_validated.input_json(input_file)
        elif args.file[0].endswith(".html"):
            fhr_to_be_validated.input_microdata(input_file)
        elif args.file[0].endswith(".gfa"):
            fhr_to_be_validated.input_gfa(input_file)
        else:
            sys.exit("Input file extention not found")

    fhr_to_be_validated.fhr_validate()
