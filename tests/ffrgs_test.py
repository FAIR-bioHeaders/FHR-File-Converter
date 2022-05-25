import unittest

from ffrgs import ffrgs

class TestFFRGS(unittest.TestCase):
    def test_yaml(self):
        test_data = "assembler:\n  name: David Molik\n  url: https:/david.molik.co/person\nassemblySoftware: HiFiASM\nauthor:\n  name: Adam Wright\n  url: https://wormbase.org/resource/person/WBPerson30813\ndateCreated: '2022-03-21'\ndocumentation: 'Built assembly from... '\nfunding: some\ngenome: Bombas huntii\nidentifier:\n- gkx10242566416842\ninstrument:\n- Sequel IIe\n- Nanopore\nlicence: public domain\nphysicalSample: Located in Freezer 33, Drawer 137\nplace:\n  name: PBARC\n  url: https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/\nrelatedLink:\n- https/david.molik.co/genome\nschema: https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/ffrgs.json\nschemaVersion: 1\nscholarlyArticle: https://doi.org/10.1371/journal.pntd.0008755\ntaxa: Bombas huntii\nversion: 0.0.1\n"
        test_ffrgs = ffrgs()
        test_ffrgs.input_yaml(test_data)
        self.assertEqual(test_data, test_ffrgs.output_yaml)

    def test_json(self):
        test_data = '{"schema": "https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/ffrgs.json", "version": "0.0.1", "schemaVersion": 1, "genome": "Bombas huntii", "author": {"name": "Adam Wright", "url": "https://wormbase.org/resource/person/WBPerson30813"}, "assembler": {"name": "David Molik", "url": "https:/david.molik.co/person"}, "place": {"name": "PBARC", "url": "https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/"}, "taxa": "Bombas huntii", "assemblySoftware": "HiFiASM", "physicalSample": "Located in Freezer 33, Drawer 137", "dateCreated": "2022-03-21", "instrument": ["Sequel IIe", "Nanopore"], "scholarlyArticle": "https://doi.org/10.1371/journal.pntd.0008755", "documentation": "Built assembly from... ", "identifier": ["gkx10242566416842"], "relatedLink": ["https/david.molik.co/genome"], "funding": "some", "licence": "public domain"}'
        test_ffrgs = ffrgs()
        test_ffrgs.input_json(test_data)
        self.assertEqual(test_data, test_ffrgs.output_json)

    def test_micodata(self):
        test_data = '<div itemscope itemtype="https://github.com/FFRGS/FFRGS-Specification" version="1"><span itemprop="schema">https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/ffrgs.json</span><span itemprop="schemaVersion">1</span><span itemprop="version">0.0.1</span><span itemprop="genome">Bombas huntii</span><span itemprop="author">  <span itemprop="name">Adam Wright</span>  <span itemprop="url">https://wormbase.org/resource/person/WBPerson30813"</span></span><span itemprop="assembler">  <span itemprop="name">David Molik</span>  <span itemprop="url">https:/david.molik.co/person"</span></span><span itemprop="place">  <span itemprop="name">PBARC</span>  <span itemprop="url">https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/"</span></span><span itemprop="taxa">Bombas huntii</span><span itemprop="assemblySoftware">HiFiASM</span><span itemprop="physicalSample">Located in Freezer 33, Drawer 137</span><span itemprop="dateCreated">2022-03-21</span><span itemprop="instrument">Sequel IIe</span><span itemprop="instrument">Nanopore</span><span itemprop="scholarlyArticle">https://doi.org/10.1371/journal.pntd.0008755</span><span itemprop="documentation">Built assembly from... </span><span itemprop="identifier">gkx10242566416842</span><span itemprop="relatedLink">https/david.molik.co/genome</span><span itemprop="funding">s</span><span itemprop="funding">o</span><span itemprop="funding">m</span><span itemprop="funding">e</span><span itemprop="licence">public domain</span></div>'
        test_ffrgs = ffrgs()
        test_ffrgs.input_microdata(test_data)
        self.assertEqual(test_data, test_ffrgs.output_microdata)

#    def test_fasta(self):
#        test_data = ";~schema: https://raw.githubusercontent.com/FFRGS/FFRGS-Specification/main/ffrgs.json\n;~schemaVersion: 1\n;~genome: Bombas huntii\n;~version: 0.0.1\n;~author:;~  name:Adam Wright\n;~  url:https://wormbase.org/resource/person/WBPerson30813\n;~assembler:;~  name:David Molik\n;~  url:https:/david.molik.co/person\n;~place:;~  name:PBARC\n;~  url:https://www.ars.usda.gov/pacific-west-area/hilo-hi/daniel-k-inouye-us-pacific-basin-agricultural-research-center/\n;~taxa: Bombas huntii\n;~assemblySoftware: HiFiASM\n;~physicalSample: Located in Freezer 33, Drawer 137\n;~dateCreated: 2022-03-21\n;~instrument: ['Sequel IIe', 'Nanopore']\n;~scholarlyArticle: https://doi.org/10.1371/journal.pntd.0008755\n;~documentation: Built assembly from... \n;~identifier: ['gkx10242566416842']\n;~relatedLink: ['https/david.molik.co/genome']\n;~funding: some\n;~licence: public domain\n"=
 #       test_ffrgs = ffrgs()
 #       test_ffrgs.input_fasta(test_data)
 #       self.assertEqual(test_data, test_ffrgs.output_fasta)

if __name__ == '__main__':
    unittest.main()
