import json
import re
from typing import Dict, List, Union

import microdata  # type: ignore
import yaml
from jsonschema import validate

with open("fhr_schema.json", "r") as f:
    schema = json.load(f)


class fhr:

    def __init__(
        self,
        schema: str = "",
        version: str = "",
        schemaVersion: int = 0,
        genome: str = "",
        assemblySoftware: str = "",
        voucherSpecimen: str = "",
        dateCreated: str = "",
        scholarlyArticle: str = "",
        documentation: str = "",
        reuseConditions: str = "",
        vitalStats: Dict[str, Union[int, str]] = {},
        masking: str = "",
        checksum: str = "",
    ) -> None:
        self.schema: str = schema
        self.version: str = version
        self.schemaVersion: int = schemaVersion
        self.genome: str = genome
        self.genomeSynonym: List[str] = []
        self.metadataAuthor: List[Dict[str, str]] = []
        self.assemblyAuthor: List[Dict[str, str]] = []
        self.accessionID: Dict[str, str] = {}
        self.taxon: Dict[str, str] = {}
        self.assemblySoftware: str = assemblySoftware
        self.voucherSpecimen: str = voucherSpecimen
        self.dateCreated: str = dateCreated
        self.instrument: List[str] = []
        self.scholarlyArticle: str = scholarlyArticle
        self.documentation: str = documentation
        self.identifier: List[str] = []
        self.relatedLink: List[str] = []
        self.funding: List[str] = []
        self.masking: str = masking
        self.vitalStats: Dict[str, Union[int, str]] = vitalStats
        self.reuseConditions: str = reuseConditions
        self.checksum: str = checksum

    def input_yaml(self, stream: str):
        data = yaml.safe_load(stream)
        self.schema = data["schema"]
        self.version = data["version"]
        self.schemaVersion = data["schemaVersion"]
        self.genome = data["genome"]
        self.taxon["name"] = data["taxon"]["name"]
        self.taxon["uri"] = data["taxon"]["uri"]
        self.metadataAuthor = data["metadataAuthor"]
        self.assemblyAuthor = data["assemblyAuthor"]
        self.dateCreated = data["dateCreated"]
        self.masking = data["masking"]
        self.checksum = data["checksum"]

        try:
            self.genomeSynonym = data["genomeSynonym"]
        except KeyError:
            self.genomeSynonym = None

        try:
            self.accessionID["url"] = data["accessionID"]["url"]
        except (KeyError, TypeError):
            self.accessionID["url"] = None

        try:
            self.taxon["name"] = data["taxon"]["name"]
            self.taxon["uri"] = data["taxon"]["uri"]
        except KeyError:
            self.taxon["name"] = None
            self.taxon["uri"] = None

        try:
            self.assemblySoftware = data["assemblySoftware"]
        except KeyError:
            self.assemblySoftware = None

        try:
            self.voucherSpecimen = data["voucherSpecimen"]
        except KeyError:
            self.voucherSpecimen = None

        try:
            self.instrument = data["instrument"]
        except KeyError:
            self.instrument = None

        try:
            self.scholarlyArticle = data["scholarlyArticle"]
        except KeyError:
            self.scholarlyArticle = None

        try:
            self.documentation = data["documentation"]
        except KeyError:
            self.documentation = None

        try:
            self.identifier = data["identifier"]
        except KeyError:
            self.identifier = None

        try:
            self.relatedLink = data["relatedLink"]
        except KeyError:
            self.relatedLink = None

        try:
            self.funding = data["funding"]
        except KeyError:
            self.funding = None

        try:
            self.vitalStats["N50"] = data["vitalStats"]["N50"]
            self.vitalStats["L50"] = data["vitalStats"]["L50"]
            self.vitalStats["L90"] = data["vitalStats"]["L90"]
            self.vitalStats["totalBasePairs"] = data["vitalStats"]["totalBasePairs"]
            self.vitalStats["numberContigs"] = data["vitalStats"]["numberContigs"]
            self.vitalStats["numberScaffolds"] = data["vitalStats"]["numberScaffolds"]
            self.vitalStats["readTechnology"] = data["vitalStats"]["readTechnology"]
        except (KeyError, TypeError):
            self.vitalStats = {
                "N50": None,
                "L50": None,
                "L90": None,
                "totalBasePairs": None,
                "numberContigs": None,
                "numberScaffolds": None,
                "readTechnology": None,
            }

        try:
            self.reuseConditions = data["reuseConditions"]
        except KeyError:
            self.reuseConditions = None

    def output_yaml(self) -> str:
        return yaml.dump(self.__dict__)

    def input_fasta(self, stream: str) -> None:
        formulated = "\n".join(
            re.sub(";~", "", line)
            for line in stream.splitlines()
            if line.startswith(";~")
        )
        self.input_yaml(formulated)

    def output_fasta(self) -> str:
        array = ";~- "
        name = "\n;~- name:"
        uri = "\n;~  uri:"
        end_span = ""

        data = (
            f";~schema: {self.schema}\n"
            f";~schemaVersion: {self.schemaVersion}\n"
            f";~genome: {self.genome}\n"
            f";~genomeSynonym:\n"
            f"{array + array.join(x + end_span for x in self.genomeSynonym)}"
            f";~version: {self.version}\n"
            f";~metadataAuthor:"
            f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.metadataAuthor)}'
            f"\n;~assemblyAuthor:"
            f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.assemblyAuthor)}'
            f";~accessionID:\n"
            f';~  name:{self.accessionID["name"]}\n'
            f';~  url:{self.accessionID["url"]}\n'
            f";~taxon:\n"
            f';~  name:{self.taxon["name"]}\n'
            f';~  uri:{self.taxon["uri"]}\n'
            f";~assemblySoftware: {self.assemblySoftware}\n"
            f";~voucherSpecimen: {self.voucherSpecimen}\n"
            f";~dateCreated: {self.dateCreated}\n"
            f";~instrument:\n"
            f"{array + array.join(x + end_span for x in self.instrument)}"
            f";~scholarlyArticle: {self.scholarlyArticle}\n"
            f";~documentation: {self.documentation}\n"
            f";~identifier:\n"
            f"{array + array.join(x + end_span for x in self.identifier)}"
            f";~relatedLink:\n"
            f"{array + array.join(x + end_span for x in self.relatedLink)}"
            f";~funding:\n"
            f"{array + array.join(x + end_span for x in self.funding)}"
            f";~masking {self.masking}\n"
            f";~vitalStats:\n"
            f';~-N50: {self.vitalStats["N50"]}\n'
            f';~-L50: {self.vitalStats["L50"]}\n'
            f';~-L90: {self.vitalStats["L90"]}\n'
            f';~-totalBasePairs: {self.vitalStats["totalBasePairs"]}\n'
            f';~-numberContigs: {self.vitalStats["numberContigs"]}\n'
            f';~-numberScaffolds: {self.vitalStats["numberScaffolds"]}\n'
            f';~-readTechnology: {self.vitalStats["readTechnology"]}\n'
            f";~reuseConditions: {self.reuseConditions}\n"
            f";~checksum: {self.checksum}\n"
        )

        return data

    def input_microdata(self, stream: str) -> None:
        data = microdata.get_items(stream)
        data = data[0]
        self.schema = data.schema
        self.version = data.version
        self.schemaVersion = data.schemaVersion
        self.genome = data.genome
        self.genomeSynonym = data.get_all("genomeSynonym")
        self.metadataAuthor = data.get_all("metadataAuthor")
        self.assemblyAuthor = data.get_all("assemblyAuthor")
        self.accessionID = data.get_all("accessionID")
        self.taxon = data.get_all("taxon")
        self.assemblySoftware = data.assemblySoftware
        self.voucherSpecimen = data.voucherSpecimen
        self.dateCreated = data.dateCreated
        self.instrument = data.get_all("instrument")
        self.scholarlyArticle = data.scholarlyArticle
        self.documentation = data.documentation
        self.identifier = data.get_all("identifier")
        self.relatedLink = data.get_all("relatedLink")
        self.funding = data.get_all("funding")
        self.masking = data.masking
        self.vitalStats = data.get_all("vitalStats")
        self.reuseConditions = data.reuseConditions
        self.checksum = data.checksum

    def output_microdata(self) -> str:
        instrument = '<span itemprop="instrument">'
        identifier = '<span itemprop="identifier">'
        relatedLink = '<span itemprop="relatedLink">'
        funding = '<span itemprop="funding">'
        metadataAuthor = '<span itemprop="metadataAuthor">'
        assemblyAuthor = '<span itemprop="assemblyAuthor">'
        genomeSynonym = '<span itemprop="genomeSynonym">'
        name = '<span itemprop="name">'
        uri = '<span itemprop="uri">'
        end_span = "</span>"

        data = (
            f'<div itemscope itemtype="https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json" version="{self.schemaVersion}">'
            f'<span itemprop="schema">{self.schema}</span>'
            f'<span itemprop="schemaVersion">{self.schemaVersion}</span>'
            f'<span itemprop="version">{self.version}</span>'
            f'<span itemprop="genome">{self.genome}</span>'
            f"{genomeSynonym + genomeSynonym.join(x + end_span for x in self.genomeSynonym)}"
            f'{metadataAuthor + metadataAuthor.join(name + x["name"] + end_span + uri + x["uri"] + end_span for x in self.metadataAuthor)}'
            f"</span>"
            f'{assemblyAuthor + assemblyAuthor.join(name + x["name"] + end_span + uri + x["uri"] + end_span for x in self.assemblyAuthor)}'
            f"</span>"
            f'<span itemprop="accessionID">'
            f'  <span itemprop="name">{self.accessionID["name"]}</span>'
            f'  <span itemprop="url">{self.accessionID["url"]}"</span>'
            f"</span>"
            f'<span itemprop="taxon">'
            f'  <span itemprop="name">{self.taxon["name"]}</span>'
            f'  <span itemprop="uri">{self.taxon["uri"]}</span>'
            f"</span>"
            f'<span itemprop="assemblySoftware">{self.assemblySoftware}</span>'
            f'<span itemprop="voucherSpecimen">{self.voucherSpecimen}</span>'
            f'<span itemprop="dateCreated">{self.dateCreated}</span>'
            f"{instrument + instrument.join(x + end_span for x in self.instrument)}"
            f'<span itemprop="scholarlyArticle">{self.scholarlyArticle}</span>'
            f'<span itemprop="documentation">{self.documentation}</span>'
            f"{identifier + identifier.join(x + end_span for x in self.identifier)}"
            f"{relatedLink + relatedLink.join(x + end_span for x in self.relatedLink)}"
            f"{funding + funding.join(x + end_span for x in self.funding)}"
            f'<span itemprop="masking">{self.masking}</span>'
            f'<span itemprop="vitalStats">'
            f'  <span itemprop="N50">{self.vitalStats["N50"]}</span>'
            f'  <span itemprop="L50">{self.vitalStats["L50"]}</span>'
            f'  <span itemprop="L90">{self.vitalStats["L90"]}</span>'
            f'  <span itemprop="totalBasePairs">{self.vitalStats["totalBasePairs"]}</span>'
            f'  <span itemprop="numberContigs">{self.vitalStats["numberContigs"]}</span>'
            f'  <span itemprop="numberScaffolds">{self.vitalStats["numberScaffolds"]}</span>'
            f'  <span itemprop="readTechnology">{self.vitalStats["readTechnology"]}</span>'
            f"</span>"
            f'<span itemprop="reuseConditions">{self.reuseConditions}</span>'
            f'<span itemprop="checksum">{self.checksum}</span>'
            f"</div>"
        )

        return data

    def input_json(self, stream: str) -> None:
        data = json.loads(stream)
        self.schema = data["schema"]
        self.version = data["version"]
        self.schemaVersion = data["schemaVersion"]
        self.genome = data["genome"]
        self.taxon["name"] = data["taxon"]["name"]
        self.taxon["uri"] = data["taxon"]["uri"]
        self.metadataAuthor = data["metadataAuthor"]
        self.assemblyAuthor = data["assemblyAuthor"]
        self.dateCreated = data["dateCreated"]
        self.masking = data["masking"]
        self.checksum = data["checksum"]
        try:
            self.genomeSynonym = data["genomeSynonym"]
        except KeyError:
            self.genomeSynonym = None

        try:
            self.accessionID["url"] = data["accessionID"]["url"]
        except (KeyError, TypeError):
            self.accessionID["url"] = None

        try:
            self.taxon["name"] = data["taxon"]["name"]
            self.taxon["uri"] = data["taxon"]["uri"]
        except KeyError:
            self.taxon["name"] = None
            self.taxon["uri"] = None

        try:
            self.assemblySoftware = data["assemblySoftware"]
        except KeyError:
            self.assemblySoftware = None

        try:
            self.voucherSpecimen = data["voucherSpecimen"]
        except KeyError:
            self.voucherSpecimen = None

        try:
            self.instrument = data["instrument"]
        except KeyError:
            self.instrument = None

        try:
            self.scholarlyArticle = data["scholarlyArticle"]
        except KeyError:
            self.scholarlyArticle = None

        try:
            self.documentation = data["documentation"]
        except KeyError:
            self.documentation = None

        try:
            self.identifier = data["identifier"]
        except KeyError:
            self.identifier = None

        try:
            self.relatedLink = data["relatedLink"]
        except KeyError:
            self.relatedLink = None

        try:
            self.funding = data["funding"]
        except KeyError:
            self.funding = None

        try:
            self.vitalStats["N50"] = data["vitalStats"]["N50"]
            self.vitalStats["L50"] = data["vitalStats"]["L50"]
            self.vitalStats["L90"] = data["vitalStats"]["L90"]
            self.vitalStats["totalBasePairs"] = data["vitalStats"]["totalBasePairs"]
            self.vitalStats["numberContigs"] = data["vitalStats"]["numberContigs"]
            self.vitalStats["numberScaffolds"] = data["vitalStats"]["numberScaffolds"]
            self.vitalStats["readTechnology"] = data["vitalStats"]["readTechnology"]
        except (KeyError, TypeError):
            self.vitalStats = {
                "N50": None,
                "L50": None,
                "L90": None,
                "totalBasePairs": None,
                "numberContigs": None,
                "numberScaffolds": None,
                "readTechnology": None,
            }

        try:
            self.reuseConditions = data["reuseConditions"]
        except KeyError:
            self.reuseConditions = None

    def output_json(self) -> str:
        return json.dumps(self.__dict__)

    def input_gfa(self, stream: str) -> None:
        formulated = "\n".join(
            re.sub("#~", "", line)
            for line in stream.splitlines()
            if line.startswith("#~")
        )
        self.input_yaml(formulated)

    def output_gfa(self) -> str:
        array = "#~- "
        name = "\n;~- name:"
        uri = "\n;~  uri:"
        end_span = ""

        data = (
            f"#~schema: {self.schema}\n"
            f"#~schemaVersion: {self.schemaVersion}\n"
            f"#~genome: {self.genome}\n"
            f"#~genomeSynonym:\n"
            f"{array + array.join(x + end_span for x in self.genomeSynonym)}"
            f"#~version: {self.version}\n"
            f"#~metadataAuthor:"
            f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.metadataAuthor)}'
            f"\n;~assemblyAuthor:"
            f'{name + name.join(name + x["name"] + uri + x["uri"] for x in self.assemblyAuthor)}'
            f"#~accessionID:\n"
            f'#~  name:{self.accessionID["name"]}\n'
            f'#~  url:{self.accessionID["url"]}\n'
            f"#~taxon:\n"
            f'#~  name:{self.taxon["name"]}\n'
            f'#~  uri:{self.taxon["uri"]}\n'
            f"#~assemblySoftware: {self.assemblySoftware}\n"
            f"#~voucherSpecimen: {self.voucherSpecimen}\n"
            f"#~dateCreated: {self.dateCreated}\n"
            f"#~instrument:\n"
            f"{array + array.join(x + end_span for x in self.instrument)}"
            f"#~scholarlyArticle: {self.scholarlyArticle}\n"
            f"#~documentation: {self.documentation}\n"
            f"#~identifier:\n"
            f"{array + array.join(x + end_span for x in self.identifier)}"
            f"#~relatedLink:\n"
            f"{array + array.join(x + end_span for x in self.relatedLink)}"
            f"#~funding:\n"
            f"{array + array.join(x + end_span for x in self.funding)}"
            f"#~masking {self.masking}\n"
            f"#~vitalStats:\n"
            f'#~-N50: {self.vitalStats["N50"]}\n'
            f'#~-L50: {self.vitalStats["L50"]}\n'
            f'#~-L90: {self.vitalStats["L90"]}\n'
            f'#~-totalBasePairs: {self.vitalStats["totalBasePairs"]}\n'
            f'#~-numberContigs: {self.vitalStats["numberContigs"]}\n'
            f'#~-numberScaffolds: {self.vitalStats["numberScaffolds"]}\n'
            f'#~-readTechnology: {self.vitalStats["readTechnology"]}\n'
            f"#~reuseConditions: {self.reuseConditions}\n"
            f"#~checksum: {self.checksum}\n"
        )

        return data

    def fhr_validate(self) -> None:
        fhr_instance = json.dumps(self.__dict__)
        validate(instance=fhr_instance, schema=schema)
