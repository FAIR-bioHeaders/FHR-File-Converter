import yaml
import json
import microdata
import re

class ffrgs:

    def __init__(self, schema=None, version=None, schemaVersion=None, genome=None, taxa=None, assemblySoftware=None, physicalSample=None, dateCreated=None, scholarlyArticle=None, documentation=None, licence=None):
        self.schema = schema
        self.version = version
        self.schemaVersion = schemaVersion
        self.genome = genome
        self.author = dict()
        self.assembler = dict()
        self.place = dict()
        self.taxa = taxa
        self.assemblySoftware = assemblySoftware
        self.physicalSample = physicalSample
        self.dateCreated = dateCreated
        self.instrument = []
        self.scholarlyArticle = scholarlyArticle
        self.documentation = documentation
        self.identifier = []
        self.relatedLink = []
        self.funding = []
        self.licence = licence

    #def __repr__(self):
    #    return "%s(schemaVersion=%r, version=%r, genome=%r)" % (
    #       self.schemaVersion, self.version, self.genome)

    #def __str__(self):
    #    return f'("{self.schemaVersion},{self.version},{self.genome}")'

    def input_yaml(self, stream: str):
        data = yaml.safe_load(stream)
        self.schema = data['schema']
        self.version = data['version']
        self.schemaVersion = data['schemaVersion']
        self.genome = data['genome']
        self.author["name"] = data["author"]["name"]
        self.author["url"] = data["author"]["url"]
        self.assembler["name"] = data["assembler"]["name"]
        self.assembler["url"] = data["assembler"]["url"]
        self.place["name"] = data["place"]["name"]
        self.place["url"] = data["place"]["url"]
        self.taxa = data["taxa"]
        self.assemblySoftware = data["assemblySoftware"]
        self.physicalSample = data["physicalSample"]
        self.dateCreated = data["dateCreated"]
        self.instrument = data["instrument"]
        self.scholarlyArticle = data["scholarlyArticle"]
        self.documentation = data["documentation"]
        self.identifier = data["identifier"]
        self.relatedLink = data["relatedLink"]
        self.funding = data["funding"]
        self.licence = data["licence"]

    def output_yaml(self):
        return yaml.dump(self.__dict__)

    def input_fasta(self, stream: str):
        formulated = ""
        data = re.findall(';~.*', stream)
        for value in stream:
            formulated = formulated + "\n" + re.sub(';~','', value)
        self.yaml(formulated)

    def output_fasta(self):
        data = (
        f';~schema: {self.schema}\n'
        f';~schemaVersion: {self.schemaVersion}\n'
        f';~genome: {self.genome}\n'
        f';~version: {self.version\n}'
        f';~author:'
        f';~  name:{self.author["name"]\n}'
        f';~  url:{self.author["url"]\n}'
        f';~assembler:'
        f';~  name:{self.assembler["name"]\n}'
        f';~  url:{self.assembler["url"]\n}'
        f';~place:'
        f';~  name:{self.place["name"]\n}'
        f';~  url:{self.place["url"]\n}'
        f';~taxa: {self.taxa\n}'
        f';~assemblySoftware: {self.assemblySoftware\n}'
        f';~physicalSample: {self.physicalSample\n}'
        f';~dateCreated: {self.dateCreated\n}'
        f';~instrument: {self.instrument\n}'
        f';~scholarlyArticle: {self.scholarlyArticle\n}'
        f';~documentation: {self.documentation\n}'
        f';~identifier: {self.identifier\n}'
        f';~relatedLink: {self.relatedLink\n}'
        f';~funding: {self.funding\n}'
        f';~licence: {self.licence\n}'
        )
        return data

    def input_microdata(self, stream: str):
        data = microdata.get_items(stream)
        data = data[0]
        self.schema = data.schema
        self.version = data.version
        self.schemaVersion = data.schemaVersion
        self.genome = data.genome
        self.author["name"] = data.author
        self.author["url"] = data.author.url
        self.assembler["name"] = data.assembler
        self.assembler["url"] = data.assembler.url
        self.place["name"] = data.place
        self.place["url"] = data.place.url
        self.taxa = data.taxa
        self.assemblySoftware = data.assemblySoftware
        self.physicalSample = data.physicalSample
        self.dateCreated = data.dateCreated
        self.instrument = data.get_all('instrument')
        self.scholarlyArticle = data.scholarlyArticle
        self.documentation = data.documentation
        self.identifier = data.get_all('identifier')
        self.relatedLink = data.get_all('relatedLink')
        self.funding = data.get_all('funding')
        self.licence = data.licence

    def output_microdata(self):
        instrument = '<span itemprop="instrument">'
        identifier = '<span itemprop="identifier">'
        relatedLink = '<span itemprop="relatedLink">'
        funding = '<span itemprop="funding">'
        end_span = "</span>"


        data = (
        f'<div itemscope itemtype="https://github.com/FFRGS/FFRGS-Specification" version="{self.schemaVersion}">'
        f'<span itemprop="schema">{self.schema}</span>'
        f'<span itemprop="schemaVersion">{self.schemaVersion}</span>'
        f'<span itemprop="version">{self.version}</span>'
        f'<span itemprop="genome">{self.genome}</span>'
        f'<span itemprop="author">'
        f'  <span itemprop="name">{self.author["name"]}</span>'
        f'  <span itemprop="url">{self.author["url"]}"</span>'
        f'</span>'
        f'<span itemprop="assembler">'
        f'  <span itemprop="name">{self.assembler["name"]}</span>'
        f'  <span itemprop="url">{self.assembler["url"]}"</span>'
        f'</span>'
        f'<span itemprop="place">'
        f'  <span itemprop="name">{self.place["name"]}</span>'
        f'  <span itemprop="url">{self.place["url"]}"</span>'
        f'</span>'
        f'<span itemprop="taxa">{self.taxa}</span>'
        f'<span itemprop="assemblySoftware">{self.assemblySoftware}</span>'
        f'<span itemprop="physicalSample">{self.physicalSample}</span>'
        f'<span itemprop="dateCreated">{self.dateCreated}</span>'
        f'{instrument + instrument.join(x + end_span for x in self.instrument)}'
        f'<span itemprop="scholarlyArticle">{self.scholarlyArticle}</span>'
        f'<span itemprop="documentation">{self.documentation}</span>'
        f'{identifier + identifier.join(x + end_span for x in self.identifier)}'
        f'{relatedLink + relatedLink.join(x + end_span for x in self.relatedLink)}'
        f'{funding + funding.join(x + end_span for x in self.funding)}'
        f'<span itemprop="licence">{self.licence}</span>'
        f'</div>')
        return data

    def input_json(self, stream: str):
        data = json.loads(stream)
        data = yaml.safe_load(stream)
        self.schema = data['schema']
        self.version = data['version']
        self.schemaVersion = data['schemaVersion']
        self.genome = data['genome']
        self.author["name"] = data["author"]["name"]
        self.author["url"] = data["author"]["url"]
        self.assembler["name"] = data["assembler"]["name"]
        self.assembler["url"] = data["assembler"]["url"]
        self.place["name"] = data["place"]["name"]
        self.place["url"] = data["place"]["url"]
        self.taxa = data["taxa"]
        self.assemblySoftware = data["assemblySoftware"]
        self.physicalSample = data["physicalSample"]
        self.dateCreated = data["dateCreated"]
        self.instrument = data["instrument"]
        self.scholarlyArticle = data["scholarlyArticle"]
        self.documentation = data["documentation"]
        self.identifier = data["identifier"]
        self.relatedLink = data["relatedLink"]
        self.funding = data["funding"]
        self.licence = data["licence"]

    def output_json(self):
        return json.dumps(self.__dict__)

#TODO   def validate(self)
