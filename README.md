# FHR-File-Converter
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6762547.svg)](https://doi.org/10.5281/zenodo.6762547)

This is the fhr file converter, it can convert fhr inbetween json, fasta, microdata, and fasta header. If you would like a detailed specification of fhr, see [FHR-Specification](https://github.com/FAIR-bioHeaders/FHR-Specification)

## Installation

You can install the FHR file converter and its dependencies using Poetry:

```bash
poetry install
```

## Usage


### Commnand line Usage

Using FHR on the command line:

```bash
fhr-convert <input>.<yaml|json|fasta|html> <output>.<yaml|json|fasta|html>
```

In more exapnsive terms:

```
usage: fhr-convert [-h] [--version] <file> <file>

Convert from one FHR supported file type to another

positional arguments:
  <file>      input followed by output

optional arguments:
  -h, --help  show this help message and exit
  --version   show program's version number and exit

positional <file> input and output files
    input files can be one of:
        <input>.yml
        <input>.fasta  - fasta contining a fhr header
        <input>.html   - html containing microdata

    output files can be one of:
        <output>.yml
        <output>.fasta - fasta output type will be made as a fasta header without sequences
        <output>.html  - microdata output type will be made into generic html output
```

## Validating an FHR file on bash command line


```bash
fhr-validate <input>.<yaml|json|fasta|html>
```

in more expansive terms:

```
usage: fhr-validate [-h] [--version] <file>

Validate a fhr containing file

 positional <file> input and output files
                        input files can be one of:
                            <input>.yml
                            <input>.fasta  - fasta contining a fhr header
                            <input>.html   - html containing microdata
```


As such validating a yaml file named "important\_genome.fhr.yml" would be:

`fhr-validate important_genome.fhr.yml`



## Using fhr in Python

How to use the fhr library on the python3 command line:

```python
>>> from fhr import fhr
>>> file = open("example.yaml")
>>> data = fhr()
>>> data.input_yaml(file.read())
>>> data.output_fasta()
";~schema: https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/fhr.json\n;~schemaVersion: 1\n;~genome: Bombas huntii\n;~version: 0.0.1\n;~author:;~  name:Adam Wright\n;~  url:https://wormbase.org/resource/person/WBPerson30813\n;~assembler:;~  name:David Molik\n;~  url:https:/david.molik.co/person\n;~place:;~  name:PBARC\n;~  url:https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/\n;~taxa: Bombas huntii\n;~assemblySoftware: HiFiASM\n;~physicalSample: Located in Freezer 33, Drawer 137\n;~dateCreated: 2022-03-21\n;~instrument: ['Sequel IIe', 'Nanopore']\n;~scholarlyArticle: https://doi.org/10.1371/journal.pntd.0008755\n;~documentation: Built assembly from... \n;~identifier: ['gkx10242566416842']\n;~relatedLink: ['https/david.molik.co/genome']\n;~funding: some\n;~reuseConditions: public domain\n"
```

## Checksums

Because fhr stores the checksum, the fasta header of the reference genome may contain the checksum for the fasta file without the header. This would happen if the fhr fasta header was written in yaml, json, or microdata, and then converted to fasta header. Using the checksum in this example is a matter of stripping the fasta header to use the checksum:

The fasta checksum in the header is the checksum of the fasta without the header use to remove the header:

```bash
cat example.fasta | grep -E -v '^;~\s?checksum'  > example.check.fasta
```

To strip the checksum:


```bash
cat example.fasta | grep -E ';~\s?checksum' | sed 's/^;~checksum://g' | sed '/\'//g'
```

## Docker Support

You can also run the FHR file converter in a Docker container. To build the Docker image:

```bash
docker build -t fhr-file-converter .
```

And then run the Docker container:

```bash
docker run -it --rm fhr-file-converter
```

