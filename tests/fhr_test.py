import unittest

from fhr_file_converter.fhr import fhr


class TestFHR(unittest.TestCase):
    def test_yaml(self):
        test_data = ("schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json\n"
"schemaVersion: 1\n"
"taxon:\n"
"  name: Bombas huntii\n"
"  uri: https://identifiers.org/taxonomy:9606\n"
"genome: Bombas huntii\n"
"genomeSynonym:\n"
"  - B. huntii\n"
"version: 0.0.1\n"
"metadataAuthor:\n"
"- name: Adam Wright\n"
"  uri: https://orcid.org/0000-0002-5719-4024\n"
"assemblyAuthor:\n"
"- name: David Molik\n"
"  uri: https://orcid.org/0000-0003-3192-6538\n"
"dateCreated: '2022-03-21'\n"
"accessionID:\n"
"  name: PBARC\n"
"  url: https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/\n"
"instrument:\n"
"- Sequel IIe\n"
"- Nanopore\n"
"voucherSpecimen: Located in Freezer 33, Drawer 137\n"
"scholarlyArticle: 10.1371/journal.pntd.0008755\n"
"assemblySoftware: HiFiASM\n"
"funding: funding\n"
"reuseConditions: public domain\n"
"documentation: 'Built assembly from... '\n"
"masking: soft-masked\n"
"identifier:\n"
"- beetlebase:TC010103\n"
"relatedLink:\n"
"- http://wfleabase.org/genome/Daphnia_pulex/dpulex_jgi060905/fasta/\n"
"checksum: md5:7582b26fcb0a9775b87c38f836e97c42'\n")
        test_fhr = fhr()
        test_fhr.input_yaml(test_data)
        self.isinstance(test_fhr, fhr)

    def test_json(self):
        test_data = '{ "$schema":"https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json", "$id":"https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/examples/example.fhr.json", "schema":"https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.jso", "schemaVersion": 1.0, "taxon" : { "name":"Bombas huntii", "uri": "https://identifiers.org/taxonomy:9606" }, "genome": "Bombas huntii", "genomeSynonym": ["B. huntii"], "version":"0.0.1", "metadataAuthor": [ { "name":"Adam Wright", "uri":"https://orcid.org/0000-0002-5719-4024" } ], "assemblyAuthor": [ { "name":"David Molik", "url":"https://orcid.org/0000-0003-3192-6538" } ], "dateCreated":"2022-03-21", "accessionID": { "name":"PBARC", "url":"https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/" }, "instrument": ["Sequel IIe", "Nanopore"], "voucherSpecimen":"Located in Freezer 33, Drawer 137", "scholarlyArticle":"10.1371/journal.pntd.0008755", "assemblySoftware":"HiFiASM", "funding":"funding", "reuseConditions":"public domain", "documentation":"Built assembly from... ", "masking":"soft-masked", "identifier": ["beetlebase:TC010103"], "relatedLink": ["http://wfleabase.org/genome/Daphnia_pulex/dpulex_jgi060905/fasta/"], "checksum":"md5:7582b26fcb0a9775b87c38f836e97c42" }'
        test_fhr = fhr()
        test_fhr.input_json(test_data)
        self.isinstance(test_fhr, fhr)

    def test_micodata(self):
        test_data = '<div itemscope itemtype="https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json" version="1"> <span itemprop="schema">https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json</span> <span itemprop="schemaVersion">1</span> <span itemprop="version">0.0.1</span> <span itemprop="genome">Bombas huntii</span> <span itemprop="genomeSynonym">B. huntii</span> <span itemprop="metadataAuthor"> <span itemprop="name">Adam Wright</span><span itemprop="uri">https://orcid.org/0000-0002-5719-4024"</span> </span> <span itemprop="assemblyAuthor"> <span itemprop="name">David Molik</span> <span itemprop="uri">https://orcid.org/0000-0003-3192-6538"</span> </span> <span itemprop="accessionID"> <span itemprop="name">PBARC</span> <span itemprop="url">https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/"</span> </span> <span itemprop="taxon"> <span itemprop="name">Bomnas huntii</span> <span itemprop="uri">https://identifiers.org/taxonomy:9606</span> </span> <span itemprop="assemblySoftware">HiFiASM</span> <span itemprop="voucherSpecimen">Located in Freezer 33, Drawer 137</span> <span itemprop="dateCreated">2022-03-21</span> <span itemprop="instrument">Sequel IIe</span> <span itemprop="instrument">Nanopore</span> <span itemprop="scholarlyArticle">https://doi.org/10.1371/journal.pntd.0008755</span> <span itemprop="documentation">Built assembly from...</span> <span itemprop="identifier">beetlebase:TC010103</span> <span itemprop="masking">soft-masked</span> <span itemprop="relatedLink">http://wfleabase.org/genome/Daphnia_pulex/dpulex_jgi060905/fasta/</span> <span itemprop="funding">some</span> <span itemprop="reuseConditions">public domain</span> <span itemprop="checksum">md5:7582b26fcb0a9775b87c38f836e97c42</span> </div>'
        test_fhr = fhr()
        test_fhr.input_microdata(test_data)
        self.isinstance(test_fhr, fhr)


#    def test_fasta(self): # noqa
#        test_data = ";~schema: https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/fhr.json\n;~schemaVersion: 1\n;~genome: Bombas huntii\n;~version: 0.0.1\n;~author:;~  name:Adam Wright\n;~  url:https://wormbase.org/resource/person/WBPerson30813\n;~assembler:;~  name:David Molik\n;~  url:https:/david.molik.co/person\n;~place:;~  name:PBARC\n;~  url:https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/\n;~taxa: Bombas huntii\n;~assemblySoftware: HiFiASM\n;~physicalSample: Located in Freezer 33, Drawer 137\n;~dateCreated: 2022-03-21\n;~instrument: ['Sequel IIe', 'Nanopore']\n;~scholarlyArticle: https://doi.org/10.1371/journal.pntd.0008755\n;~documentation: Built assembly from... \n;~identifier: ['gkx10242566416842']\n;~relatedLink: ['https/david.molik.co/genome']\n;~funding: some\n;~licence: public domain\n"= # noqa
#       test_fhr = fhr() # noqa
#       test_fhr.input_fasta(test_data) # noqa
#       self.assertEqual(test_data, test_fhr.output_fasta) # noqa


if __name__ == "__main__":
    unittest.main()
