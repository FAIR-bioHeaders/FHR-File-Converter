# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""JSON-LD for FHR metadata: the writer and the canonical reader (provisional API).

The JSON-LD form is the FHR record with its own keys, an embedded ``@context``
and ``@type`` on the record and its nested nodes (FHR-Specification
docs/JSONLD.md, feature 011). The bundled ``fhr.context.jsonld`` is a
byte-identical copy of FHR-Specification ``jsonld/fhr.context.jsonld``.

Writing and canonical reading (rule J1) need only the standard library and never
use the network. Reading JSON-LD in other forms (rules J3 to J5) is not
supported yet.
"""

import copy
import json
import re
import sys
from importlib.resources import files

CONTEXT = json.loads(
    files(__package__).joinpath("fhr.context.jsonld").read_text(encoding="utf-8")
)
RAW_MAIN_CONTEXT_URL = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/"
    "jsonld/fhr.context.jsonld"
)
# (version, context document) for every bundled context. No FHR-Specification
# release contains the context yet, so the only one is that of main; release
# versions are added, with their raw tag and w3id URLs, once they exist.
BUNDLED_CONTEXTS = (("main", CONTEXT),)


def _context_urls(version):
    if version == "main":
        return (RAW_MAIN_CONTEXT_URL,)
    return (
        "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/"
        f"{version}/jsonld/fhr.context.jsonld",
        f"https://w3id.org/fair-bioheaders/fhr/{version}/jsonld/fhr.context.jsonld",
    )


# Context URLs that a canonical document may reference; nothing is fetched.
KNOWN_CONTEXT_URLS = tuple(
    url for version, _ in BUNDLED_CONTEXTS for url in _context_urls(version)
)
# The Bioschemas Dataset release whose minimum properties are checked; Dataset
# 1.1 was still a draft on 2026-10-10 (https://bioschemas.org/profiles/).
BIOSCHEMAS_DATASET_PROFILE = "https://bioschemas.org/profiles/Dataset/1.0-RELEASE"
# Its minimum properties beside @context, @type and dct:conformsTo, with the key
# that carries each one in a written document.
BIOSCHEMAS_MINIMUM = (
    ("@id", "@id"),
    ("description", "documentation"),
    ("identifier", "identifier"),
    ("keywords", "keywords"),
    ("license", "reuseConditions"),
    ("name", "genome"),
    ("url", "url"),
)
NODE_TYPES = {
    "taxon": "Taxon",
    "accessionID": "PropertyValue",
    "vitalStats": "VitalStats",
}
AUTHOR_KEYS = ("metadataAuthor", "assemblyAuthor")
# The fhr.json orcidUri pattern (a prefix match) and the ROR identifier form.
ORCID_URI = re.compile(r"https://orcid\.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]")
ROR_URI = re.compile(r"https://ror\.org/0[0-9a-z]{6}[0-9]{2}")
# An absolute URL: a scheme, "://", and no whitespace.
ABSOLUTE_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://\S+")
URL_TERM = "subjectOf"
EXPORT_KEYS = ("id", "url", "keywords")
# Root keys of a written document that carry export metadata, not FHR fields.
EXPORT_OUTPUT = ("@id", "keywords", "url", "conformsTo")
NOT_CANONICAL = (
    "this JSON-LD is not in the canonical FAIR-bioHeaders form (rule J1 of "
    "FHR-Specification docs/JSONLD.md); reading other JSON-LD forms is not "
    "supported yet"
)


def _print_warning(message):
    print(f"FHR: {message}", file=sys.stderr)


def author_type(item):
    """``Person`` for an ORCID ``uri``, ``Organization`` for ROR, else ``Agent``."""
    uri = item.get("uri")
    if isinstance(uri, str) and ORCID_URI.match(uri):
        return "Person"
    if isinstance(uri, str) and ROR_URI.fullmatch(uri):
        return "Organization"
    return "Agent"


def is_absolute_url(value):
    return isinstance(value, str) and ABSOLUTE_URL.fullmatch(value) is not None


def check_export(export):
    """Validate an export context: optional ``id``, ``url`` and ``keywords``."""
    if not isinstance(export, dict):
        raise ValueError(
            "export context must be a mapping with id, url and/or keywords"
        )
    unknown = sorted(str(key) for key in set(export) - set(EXPORT_KEYS))
    if unknown:
        raise ValueError(
            f"export context: unknown key {', '.join(unknown)}; "
            "allowed: id, url, keywords"
        )
    for key in ("id", "url"):
        if key in export and not is_absolute_url(export[key]):
            raise ValueError(f"export context: {key} must be an absolute URL")
    keywords = export.get("keywords", ["x"])
    if not (
        isinstance(keywords, list)
        and keywords
        and all(isinstance(word, str) and word.strip() for word in keywords)
    ):
        raise ValueError(
            "export context: keywords must be a non-empty list of non-empty strings"
        )
    return export


def _present(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def bioschemas_missing(document):
    """The Bioschemas Dataset minimum properties that a written document lacks."""
    return [name for name, key in BIOSCHEMAS_MINIMUM if not _present(document.get(key))]


def _check_reserved(value, path):
    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}.{key}" if path else key
            if key.startswith("@"):
                raise ValueError(
                    f"JSON-LD: {here} starts with @, which JSON-LD reserves; "
                    "it cannot be written"
                )
            _check_reserved(item, here)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_reserved(item, f"{path}[{index}]")


def _typed_items(value, kind):
    return [
        (
            {"@type": kind(item), **copy.deepcopy(item)}
            if isinstance(item, dict)
            else copy.deepcopy(item)
        )
        for item in value
    ]


def _typed(key, value):
    if key in NODE_TYPES and isinstance(value, dict):
        return {"@type": NODE_TYPES[key], **copy.deepcopy(value)}
    if key in AUTHOR_KEYS and isinstance(value, list):
        return _typed_items(value, author_type)
    if key == "assemblySoftware" and isinstance(value, list):
        return _typed_items(value, lambda item: "SoftwareApplication")
    return copy.deepcopy(value)


def to_jsonld(data, export=None):
    """Return the JSON-LD document for FHR metadata ``data`` (rule J7).

    ``export`` is an optional export context (``id``, ``url``, ``keywords``);
    ``conformsTo`` the Bioschemas Dataset profile is added only when every
    minimum property of that profile is present.
    """
    _check_reserved(data, "")
    for key in (URL_TERM, *EXPORT_OUTPUT):
        if key in data:
            raise ValueError(
                f"JSON-LD: the root key {key} is reserved for JSON-LD output"
            )
    if export is not None:
        export = check_export(export)
    document = {"@context": CONTEXT["@context"], "@type": "Dataset"}
    if export and "id" in export:
        document["@id"] = export["id"]
    for key, value in data.items():
        if key == "documentation" and is_absolute_url(value):
            document[URL_TERM] = value
        else:
            document[key] = _typed(key, value)
    if export:
        for key in ("keywords", "url"):
            if key in export:
                document[key] = copy.deepcopy(export[key])
        if not bioschemas_missing(document):
            document["conformsTo"] = BIOSCHEMAS_DATASET_PROFILE
    return document


def _scope_terms():
    root = CONTEXT["@context"]
    terms = {}
    for key in ("taxon", *AUTHOR_KEYS, "accessionID", "vitalStats"):
        body = root[key]["@context"][1]
        terms[key] = {
            term
            for term, value in body.items()
            if isinstance(value, dict) or value == "@id"
        }
    return terms


SCOPE_TERMS = _scope_terms()


def unmapped_keys(data):
    """Paths of nested keys that the context does not define, such as
    ``taxon.checksum`` or ``assemblyAuthor[0].affiliation``."""
    found = []
    for key, value in data.items():
        if key not in SCOPE_TERMS:
            continue
        if isinstance(value, dict):
            items = [(key, value)]
        elif isinstance(value, list):
            items = [
                (f"{key}[{index}]", item)
                for index, item in enumerate(value)
                if isinstance(item, dict)
            ]
        else:
            items = []
        for path, item in items:
            found += [f"{path}.{name}" for name in item if name not in SCOPE_TERMS[key]]
    return found


def _plain(node, root):
    """True if ``node`` has no JSON-LD keyword except @type (and root @context/@id)."""
    if isinstance(node, list):
        return all(_plain(item, False) for item in node)
    if not isinstance(node, dict):
        return True
    for key, item in node.items():
        if key == "@type":
            if not (
                isinstance(item, str)
                or isinstance(item, list)
                and all(isinstance(kind, str) for kind in item)
            ):
                return False
        elif key.startswith("@"):
            if not (root and key in ("@context", "@id")):
                return False
        elif not _plain(item, False):
            return False
    return True


def is_canonical(document):
    """Rule J1: a bundled context, embedded or by a known URL, and no keyword
    except ``@type`` on objects and an optional root ``@id``."""
    if not isinstance(document, dict) or "@context" not in document:
        return False
    value = document["@context"]
    if isinstance(value, str):
        if value not in KNOWN_CONTEXT_URLS:
            return False
    elif not any(value == bundled["@context"] for _, bundled in BUNDLED_CONTEXTS):
        return False
    if "@id" in document and not isinstance(document["@id"], str):
        return False
    return _plain(document, True)


def _without_types(value):
    if isinstance(value, dict):
        return {k: _without_types(item) for k, item in value.items() if k != "@type"}
    if isinstance(value, list):
        return [_without_types(item) for item in value]
    return value


def from_jsonld(document, *, ignore_unknown_terms=False, warn=None):
    """Return the FHR metadata of a JSON-LD document (rule J1).

    ``@context`` and every ``@type`` are set aside, a root ``subjectOf`` is the
    ``documentation`` value, and the export terms ``@id``, ``keywords``, ``url``
    and ``conformsTo`` are set aside with a warning passed to ``warn`` (default:
    print to stderr). ``ignore_unknown_terms`` is reserved for reading other
    JSON-LD forms and has no effect on canonical documents. Raises
    ``ValueError`` for anything else.
    """
    warn = _print_warning if warn is None else warn
    if not isinstance(document, dict):
        raise ValueError("JSON-LD metadata must be a JSON object")
    if not is_canonical(document):
        raise ValueError(NOT_CANONICAL)
    record = {}
    for key, value in document.items():
        if key in ("@context", "@type"):
            continue
        if key in EXPORT_OUTPUT:
            warn(
                f"JSON-LD: {key} is export metadata, not an FHR field; it was not kept"
            )
            continue
        if key == URL_TERM:
            if "documentation" in document:
                raise ValueError("JSON-LD gives both documentation and subjectOf")
            if not isinstance(value, str):
                raise ValueError("JSON-LD subjectOf must be a string")
            key = "documentation"
        record[key] = _without_types(value)
    return record
