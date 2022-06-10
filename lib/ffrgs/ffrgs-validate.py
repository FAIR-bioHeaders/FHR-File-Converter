import argparse
import textwrap
import sys

from ffrgs import ffrgs

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Validate a FFRGS metadata file',
            epilog=textwrap.dedent('''\
                    positional <file> input and output files
                        input files can be one of:
                            <input>.yml
                            <input>.fasta  - fasta contining a ffrgs header
                            <input>.html   - html containing microdata
                            '''))

    parser.add_argument('file', 
            nargs=1,
            metavar='<file>',
            help='input followed by output')

    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1')

    args = parser.parse_args()

    ffrgs_to_be_validated = ffrgs()

    with open(args.file[0], 'r') as input_file:
        if args.file[0].endswith(".yml") or args.file[0].endswith(".yaml"):
            ffrgs_to_be_validated.input_yaml(input_file)
        elif args.file[0].endswith(".fasta") or args.file[0].endswith(".fa"):
            ffrgs_to_be_validated.input_fasta(input_file)
        elif args.file[0].endswith(".json"):
            ffrgs_to_be_validated.input_json(input_file)
        elif args.file[0].endswith(".html"):
            ffrgs_to_be_validated.input_microdata(input_file)
        else:
            sys.exit('Input file extention not found')

    ffrgs_to_be_validated.ffrgs_validate()
