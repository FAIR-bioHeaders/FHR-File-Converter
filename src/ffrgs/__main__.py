import argparse
import textwrap

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Convert from one FFRGS supported file type to another',
            epilog=textwrap.dedent('''\
                    positional <file> input and output files
                        input files can be one of:
                            <input>.yml
                            <input>.fasta  - fasta contining a ffrgs header
                            <input>.html   - html containing microdata
 
                        output files can be one of:
                            <output>.yml
                            <output>.fasta - fasta output type will be made as a fasta header without sequences
                            <output>.html  - microdata output type will be made into generic html output
                            '''))

    parser.add_argument('file', 
            nargs=2,
            metavar='<file>',
            help='input followed by output')

    parser.add_argument('--version', action='version', version='%(prog)s 0.0.1')

    args = parser.parse_args()


