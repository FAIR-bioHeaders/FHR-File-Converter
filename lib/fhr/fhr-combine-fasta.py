import argparse
import textwrap
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
                        input files can be one of:
                            <input>.yml
                            <input>.fasta  - fasta contining a ffrgs header
                            <input>.html   - html containing microdata

                            second input must be a fasta file
                            '''))

    parser.add_argument('file', 
            nargs=2,
            metavar='<file>',
            help='input followed by fasta output')

    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1')

    args = parser.parse_args()

    fhr_to_be_combined = ffrgs()

    with open(args.file[0], 'r') as input_file:
        if args.file[0].endswith(".yml") or args.file[0].endswith(".yaml"):
            fhr_to_be_combined.input_yaml(input_file)
        elif args.file[0].endswith(".fasta") or args.file[0].endswith(".fa"):
            fhr_to_be_combined.input_fasta(input_file)
        elif args.file[0].endswith(".json"):
            fhr_to_be_combined.input_json(input_file)
        elif args.file[0].endswith(".html"):
            fhr_to_be_combined.input_microdata(input_file)
        else:
            sys.exit('Input file extention not found')

    output_filename = os.path.splitext(args.file[1])[0] + ".fhr.fasta"

        with open(args.file[0], "r") as sources:
            fasta_lines = sources.readlines()    

    with open(output_filename, 'w') as output_file:
        print(fhr_to_be_combined.output_fasta())
        for line in fasta_lines:
            sources.write(line)

