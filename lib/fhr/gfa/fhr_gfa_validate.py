import argparse
import textwrap
import hashlib
import sys
import os
import re

from fhr import fhr


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Validate a FHR metadata file',
        epilog=textwrap.dedent('''\
                    positional <file> input and output files
                        input files must be:
                            <input>.gfa  - gfa contining a fhr header
                            '''))

    parser.add_argument('file',
                        nargs=1,
                        metavar='<file>',
                        help='input followed by gfa output')

    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1')

    args = parser.parse_args()

    fhr_to_be_validated = fhr()

    with open(args.file[0], 'r') as input_file:
        if args.file[0].endswith(".yml") or args.file[0].endswith(".yaml"):
            sys.exit('Input file not of correct extention')
        elif args.file[0].endswith(".fasta") or args.file[0].endswith(".fa"):
            sys.exit('Input file not of correct extention')
        elif args.file[0].endswith(".json"):
            sys.exit('Input file not of correct extention')
        elif args.file[0].endswith(".html"):
            sys.exit('Input file not of correct extention')
        elif args.file[0].endswith(".gfa"):
            fhr_to_be_validated.input_gfa(input_file)
        else:
            sys.exit('Input file extention not found')

    with open(input_file_path, 'r') as input_file:
        if file_extension == ".gfa":
            fhr_to_be_validated.input_gfa(input_file)

    temp_file_path = input_file_path + ".tmp"

    with open(temp_file_path, "w") as temp_file:
        for line in input_file:
            modified_line = re.sub(r'^#~checksum.*', '', line)
            temp_file.write(modified_line)

    with open(temp_file_path, 'rb') as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()

    if fhr_to_be_validated.checksum == md5_returned:
        print("Checksum verified.")
    else:
        print("Checksum verification failed!")

    os.remove(temp_file)
