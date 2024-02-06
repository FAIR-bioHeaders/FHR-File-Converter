import argparse
import textwrap
import sys
import re

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Validate a FHR metadata file',
            epilog=textwrap.dedent('''\
                    positional <file> input and output files
                        input files must be:
                            <input>.fasta  - fasta contining a ffrgs header
                            '''))

    parser.add_argument('file',
            nargs=1,
            metavar='<file>',
            help='input followed by output')

    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1')

    args = parser.parse_args()

    with open(args.file[0], "r") as sources:
            lines = sources.readlines()
    with open(args.file[1], "w") as sources:
            for line in lines:
                   sources.write(re.sub(r'^;~.*', '', line))

