import yaml
import json
import microdata
import re
from jsonschema import validate

schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
  "title": "FHR",
  "description": "FAIR Header Reference genomeSchema for Genome Assemblies",
  "type": "object",
  "properties": {
    "schema":{
      "type": "string",
      "description": "centralized schema file"
    },
    "schemaVersion":{
      "type": "number",
      "description": "Version of FHR"
    },
    "genome":{
      "type": "string",
      "description": "Name of the Genome"
    },
    "genomeSynonym": {
      "type": "array",
      "description": "Other common names of the genome",
      "items": {
        "type":"string"
      }
    },
    "taxon":{
      "type": "object",
      "description": "Species name and URL of the species information at identifiers.org",
      "properties": {
        "name": {
          "type": "string"
        },
        "uri": {
          "type": "string",
          "format": "uri",
          "pattern": "https://identifiers.org/taxonomy:[0-9]+"
        }
      }
    },
    "version":{
      "type": "string",
      "description": "Version number of Genome eg. 1.2.0"
    },
    "metadataAuthor":{
      "type": "array",
      "items": {
        "type": "object",
        "description": "Author of the fhr Instance (Person or Org)",
        "properties": {
          "name": {
            "type": "string"
          },
          "uri": { "$ref": "#/definitions/orcidUri" }
        }
      }
    },
    "assemblyAuthor":{
      "type": "array",
        "items": {
        "type": "object",
        "description": "Assembler of the Genome (Person or Org)",
        "properties": {
          "name": {
            "type": "string"
          },
          "uri": { "$ref": "#/definitions/orcidUri" }
        }
      }
    },
    "dateCreated":{
      "type": "string",
      "format": "date",
      "description": "Date the genome assembly was created"
    },
    "physicalSample":{
      "type": "string",
      "description": "Description of the physical sample"
    },
    "voucherId":{
      "type": "object",
      "description": "voucherId genome assembly was created",
      "properties": {
        "name": {
          "type": "string"
        },
        "url": {
          "type": "string",
          "format": "uri"
        }
      }
    },
    "instrument": {
      "type": "array",
      "description": "Physical tools and instruments used in the creation of the genome assembly",
      "items": {
        "type": "string"
      }
    },
    "scholarlyArticle": {
      "type": "string",
      "pattern": "^10.",
      "description": "Scholarly article genome was published e.g. 10.5281/zenodo.6762550 "
    },
    "documentation": {
      "type": "string",
      "description": "Documentation about the genome"
    },
    "identifier": {
      "type": "array",
      "description": "Identifies of the genome",
      "items": {
        "type": "string",
        "pattern": "[a-z0-9]*:.*"
        }
    },
    "relatedLink": {
      "type": "array",
      "description": "Related URLS to the genome",
      "items": {
        "type": "string",
        "format": "uri"
      }
    },
    "funding": {
      "type": "string",
      "description": "Grant Line Item"
    },
    "license": {
      "type": "string",
      "description": "license for the use of the Genome"
    },
    "checksum": { "$ref": "#/definitions/sha2" }
  },
  "required": [
    "schema",
    "schemaVersion",
    "genome",
    "taxon",
    "version",
    "metadataAuthor",
    "assemblyAuthor",
    "dateCreated",
    "checksum"
  ],
  "definitions": {
    "orcidUri": { "format": "uri", 
                  "pattern": "^https://orcid.org/[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9X]" },
    "sha2": {
      "type": "string",
      "minLength": 44,
      "maxLength": 44,
      "pattern": "^[A-Za-z0-9/+=]+$",
      "description": "sha2-512/256 checksum value for hashing"
    }
  }
}

class fhr:

    def __init__(self, schema=None, version=None, schemaVersion=None, genome=None, assemblySoftware=None, physicalSample=None, dateCreated=None, scholarlyArticle=None, documentation=None, licence=None, checksum=None):
        self.schema = schema
        self.version = version
        self.schemaVersion = schemaVersion
        self.genome = genome
        self.genomeSynonym = []
        self.metadataAuthor = []
        self.assemblyAuthor = []
        self.voucherId = dict()
        self.taxon = dict()
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
        self.checksum = checksum

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
        self.genomeSynonym = data['genomeSynonym']
        self.metadataAuthor = data["metadataAuthor"]
        self.assemblyAuthor = data["assemblyAuthor"]
        self.voucherId["name"] = data["voucherID"]["name"]
        self.voucherId["url"] = data["voucherId"]["url"]
        self.taxon["name"] = data["taxon"]["name"]
        self.taxon["uri"] = data["taxon"]["uri"]
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
        self.checksum = data["checksum"]

    def output_yaml(self):
        return yaml.dump(self.__dict__)

    def input_fasta(self, stream: str):
        formulated = ""
        data = re.findall(';~.*', stream)
        for value in stream:
            formulated = formulated + "\n" + re.sub(';~','', value)
        self.yaml(formulated)

    def output_fasta(self):
        name =  '<span itemprop="name">'
        uri = '<span itemprop="uri">'
        end_span = "</span>"        

        array = ';~- '
        name = '\n;~- name:'
        uri = '\n;~  uri:'

        data = (
        f';~schema: {self.schema}\n'
        f';~schemaVersion: {self.schemaVersion}\n'
        f';~genome: {self.genome}\n'
        f';~genomeSynonym:\n'
        f'{array + array.join(x + end_span for x in self.genomeSynonym)}'
        f';~version: {self.version}\n'
        f';~metadataAuthor:'
        f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.metadataAuthor)}'
        f'\n;~assemblyAuthor:'
        f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.assemblyAuthor)}'
        f';~voucherId:\n'
        f';~  name:{self.voucherId["name"]}\n'
        f';~  url:{self.voucherId["url"]}\n'
        f';~taxon:\n'
        f';~  name:{self.taxon["name"]}\n'
        f';~  uri:{self.taxon["uri"]}\n'
        f';~assemblySoftware: {self.assemblySoftware}\n'
        f';~physicalSample: {self.physicalSample}\n'
        f';~dateCreated: {self.dateCreated}\n'
        f';~instrument:\n'
        f'{array + array.join(x + end_span for x in self.instrument)}'
        f';~scholarlyArticle: {self.scholarlyArticle}\n'
        f';~documentation: {self.documentation}\n'
        f';~identifier:\n' 
        f'{array + array.join(x + end_span for x in self.identifier)}'
        f';~relatedLink:\n' 
        f'{array + array.join(x + end_span for x in self.relatedLink)}'
        f';~funding:\n'
        f'{array + array.join(x + end_span for x in self.funding)}'
        f';~licence: {self.licence}\n'
        f';~checksum: {self.checksum}\n'
        )
        return data

    def input_microdata(self, stream: str):
        data = microdata.get_items(stream)
        data = data[0]
        self.schema = data.schema
        self.version = data.version
        self.schemaVersion = data.schemaVersion
        self.genome = data.genome
        self.genomeSynonym = data.get_all('genomeSynonym')
        self.metadataAuthor = data.get_all('metadataAuthor')
        self.assemblyAuthor = data.get_all('assemblyAuthor')
        self.voucherId["name"] = data.voucherId
        self.voucherId["url"] = data.voucherId.url
        self.taxon["name"] = data.taxon.name
        self.taxon["uri"] = data.taxon.uri
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
        self.checksum = data.checksum

    def output_microdata(self):
        instrument = '<span itemprop="instrument">'
        identifier = '<span itemprop="identifier">'
        relatedLink = '<span itemprop="relatedLink">'
        funding = '<span itemprop="funding">'
        metadataAuthor = '<span itemprop="metadataAuthor">'
        assemblyAuthor = '<span itemprop="assemblyAuthor">'
        genomeSynonym = '<span itemprop="genomeSynonym">'
        name =  '<span itemprop="name">'
        uri = '<span itemprop="uri">'
        end_span = "</span>"


        data = (
        f'<div itemscope itemtype="https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json" version="{self.schemaVersion}">'
        f'<span itemprop="schema">{self.schema}</span>'
        f'<span itemprop="schemaVersion">{self.schemaVersion}</span>'
        f'<span itemprop="version">{self.version}</span>'
        f'<span itemprop="genome">{self.genome}</span>'
        f'{genomeSynonym + genomeSynonym.join(x + end_span for x in self.genomeSynonym)}'
        f'{metadataAuthor + metadataAuthor.join(name + x["name"] + end_span + uri + x["uri"] + end_span for x in self.metadataAuthor)}'
        f'</span>'
        f'{assemblyAuthor + assemblyAuthor.join(name + x["name"] + end_span + uri + x["uri"] + end_span for x in self.assemblyAuthor)}'
        f'</span>'
        f'<span itemprop="voucherId">'
        f'  <span itemprop="name">{self.voucherId["name"]}</span>'
        f'  <span itemprop="url">{self.voucherId["url"]}"</span>'
        f'</span>'
        f'<span itemprop="taxon">'
        f'  <span itemprop="name">self.taxon["name"]</span>'
        f'  <span itemprop="uri">self.taxon["uri"]</span>'
        f'</span>'
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
        f'<span itemprop="checksum">{self.checksum}</span>'
        f'</div>')
        return data

    def input_json(self, stream: str):
        data = json.loads(stream)
        data = yaml.safe_load(stream)
        self.schema = data['schema']
        self.version = data['version']
        self.schemaVersion = data['schemaVersion']
        self.genome = data['genome']
        self.genomeSynonym = data['genomeSynonym']
        self.metadataAuthor = data["metadataAuthor"]
        self.assemblyAuthor = data["assemblyAuthor"]
        self.voucherId["name"] = data["voucherId"]["name"]
        self.voucherId["url"] = data["voucherId"]["url"]
        self.taxon["name"] = data["taxon"]["name"]
        self.taxon["uri"] = data["taxon"]["uri"]
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
        self.checksum = data["checksum"]

    def output_json(self):
        return json.dumps(self.__dict__)

    def fhr_validate(self):
        fhr_instance = json.dumps(self.__dict__)
        validate(instance=fhr_instance, schema=schema)
