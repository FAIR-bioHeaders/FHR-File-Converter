import yaml
import json
import microdata
import re
from typing import overload

class ffrgs:

    def __init__(self, version=0, schemaVersion=0, genome=None):
    #def __init__(self, version, genome, author, assembler, place, taxa, assemblySoftware, physicalSample, dateCreated, scholarlyArticle, documentationi, licence):
        self.version = version
        self.schemaVersion = schemaVersion
        self.genome = genome
        #self.author = author
        #self.assembler = assembler
        #self.place = place
        #self.taxa = taxa
        #self.assemblySoftware = assemblySoftware
        #self.physicalSample = physicalSample
        #self.dateCreated = dateCreated
        #self.instrument = []
        #self.scholarlyArticle = scholarlyArticle
        #self.documentation = documentation
        #self.identifier = []
        #self.relatedLink = []
        #self.funding = []
        #self.licence = licence

    def __repr__(self):
        return "%s(schemaVersion=%r, version=%r, genome=%r)" % (
            self.schemaVersion, self.version, self.genome)

    def __str__(self):
        return f'("{self.schemaVersion},{self.version},{self.genome}")'

    @overload
    def yaml(self, stream: str):
        data = yaml.safe_load(stream)
        self.version = data['version']
        self.schemaVersion = data['schemaVersion']
        self.genome = data['genome']

    def yaml(self):
        yaml.dump(self.__dict__)

    @overload
    def fasta(self, stream: str):
        formulated = ""
        data = re.findall(';~.*', stream)
        for value in stream:
            formulated = formulated + "\n" + re.sub(';~','', value)
        self.yaml(formulated)

    def fasta(self):
        data = (
        f';~schemaVersion: {self.schemaVersion}'
        f';~genome: {self.genome}'
        f';~version: {self.version}'
        )
        return data

    @overload 
    def microdata(self, stream: str):
        data = microdata.get_items(stream)
        data = data[0]
        self.version = data.version
        self.schemaVersion = data.schemaVersion
        self.genome = data.genome

    def microdata(self):
        data = (
        f'<div itemscope itemtype="https://github.com/FFRGS/FFRGS-Specification" version="{self.schemaVersion}">'
        f'<span itemprop="schemaVersion">{self.schemaVersion}</span>'
        f'<span itemprop="version">{self.version}</span>'
        f'<span itemprop="genome">{self.genome}</span>'
        f'</div>')
        return data

    @overload
    def json(self, stream: str):
        data = json.loads(stream)
        self.version = data["version"]
        self.schemaVersion = data["schemaVersion"]
        self.genome = data["genome"]

    def json(self):
        json.dumps(self.__dict__)

#TODO   def validate(self)
