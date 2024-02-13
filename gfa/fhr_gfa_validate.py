import argparse
import hashlib
import os
import re
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
                        input files must be:
                            <input>.gfa  - gfa contining a fhr header
                            """
        ),
    )

    parser.add_argument(
        "file", nargs=1, metavar="<file>", help="input followed by gfa output"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.0.1")

    args = parser.parse_args()

    fhr_to_be_validated = fhr()

    input_filepath = args.file[0]

    with open(input_filepath, "r") as input_file:
        if input_filepath.endswith(".yml") or input_filepath.endswith(".yaml"):
            sys.exit("Input file not of correct extention")
        elif input_filepath.endswith(".fasta") or input_filepath.endswith(".fa"):
            sys.exit("Input file not of correct extention")
        elif input_filepath.endswith(".json"):
            sys.exit("Input file not of correct extention")
        elif input_filepath.endswith(".html"):
            sys.exit("Input file not of correct extention")
        elif input_filepath.endswith(".gfa"):
            fhr_to_be_validated.input_gfa(input_file)
        else:
            sys.exit("Input file extention not found")

    temp_filepath = input_filepath + ".tmp"

    with open(temp_filepath, "w") as temp_file:
        for line in input_file:
            modified_line = re.sub(r"^#~checksum.*", "", line)
            temp_file.write(modified_line)

    with open(temp_filepath, "rb") as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()

    if fhr_to_be_validated.checksum == md5_returned:
        print("Checksum verified.")
    else:
        print("Checksum verification failed!")

    os.remove(temp_file)
