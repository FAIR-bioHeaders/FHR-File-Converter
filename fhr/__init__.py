"""FHR metadata parsing, serialization, and validation."""

import json
from copy import deepcopy
from datetime import date, datetime
from html import escape
from html.parser import HTMLParser
from importlib.resources import files

import yaml
from jsonschema import Draft202012Validator, FormatChecker

__version__ = "0.3.0"
SCHEMA = json.loads(
    files(__package__).joinpath("fhr_schema.json").read_text(encoding="utf-8")
)
ITEM_TYPE = SCHEMA["$id"]


def _text(stream):
    value = stream.read() if hasattr(stream, "read") else stream
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if not isinstance(value, str):
        raise TypeError("Expected text or a readable stream")
    return value


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Metadata object keys must be strings")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


class _MetadataHTML(HTMLParser):
    """Parse FHR item scopes, using explicit JSON types for lossless values."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.result = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self._leaf(attrs)
            return
        root = "itemscope" in attrs and attrs.get("itemtype") == ITEM_TYPE
        if not self.stack and not root:
            return
        if root and (self.result is not None or self.stack):
            raise ValueError("Multiple FHR item scopes found")
        self.stack.append({"tag": tag, "attrs": attrs, "text": [], "values": {}})

    def handle_startendtag(self, tag, attrs):
        self._leaf(dict(attrs))

    def _leaf(self, attrs):
        if self.stack and attrs.get("itemprop"):
            value = attrs.get("content", attrs.get("href", attrs.get("src", "")))
            self._attach(attrs["itemprop"], value)

    def handle_data(self, text):
        if self.stack:
            self.stack[-1]["text"].append(text)

    def _attach(self, key, value):
        self.stack[-1]["values"].setdefault(key, []).append(value)

    @staticmethod
    def _object(values):
        return {
            key: items[0] if len(items) == 1 else items for key, items in values.items()
        }

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]["tag"] != tag:
            return
        node = self.stack.pop()
        attrs = node["attrs"]
        kind = attrs.get("data-fhr-type")
        if tag == "time" and "datetime" in attrs:
            text = attrs["datetime"]
        elif tag in {"data", "meter"} and "value" in attrs:
            text = attrs["value"]
        else:
            text = attrs.get(
                "content", attrs.get("href", attrs.get("src", "".join(node["text"])))
            )
        if kind != "string":
            text = text.strip()
        if kind == "array":
            value = node["values"].get("item", [])
        elif kind == "object" or "itemscope" in attrs or node["values"]:
            value = self._object(node["values"])
        elif kind in {"integer", "number", "boolean", "null"}:
            value = json.loads(text)
        else:
            value = text
        if self.stack:
            if attrs.get("itemprop"):
                self._attach(attrs["itemprop"], value)
            elif "itemscope" not in attrs:
                self.stack[-1]["text"].extend(node["text"])
                for key, items in node["values"].items():
                    self.stack[-1]["values"].setdefault(key, []).extend(items)
        else:
            self.result = value


def _html_value(key, value):
    prop = escape(key, quote=True)
    if isinstance(value, dict):
        content = "".join(_html_value(k, v) for k, v in value.items())
        return (
            f'<span itemprop="{prop}" itemscope data-fhr-type="object">{content}</span>'
        )
    if isinstance(value, list):
        content = "".join(_html_value("item", v) for v in value)
        return f'<span itemprop="{prop}" data-fhr-type="array">{content}</span>'
    kind = "string"
    if value is None:
        kind = "null"
    elif isinstance(value, bool):
        kind = "boolean"
    elif isinstance(value, int):
        kind = "integer"
    elif isinstance(value, float):
        kind = "number"
    content = value if isinstance(value, str) else json.dumps(value)
    return f'<span itemprop="{prop}" data-fhr-type="{kind}">{escape(content)}</span>'


class fhr:
    """A metadata mapping. Optional fields are absent until explicitly supplied."""

    def __init__(self, **metadata):
        self.__dict__.update(deepcopy(metadata))

    def _input(self, data):
        if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
            raise ValueError("FHR metadata must be an object with string keys")
        normalized = _json_value(data)
        json.dumps(normalized, allow_nan=False)
        self.__dict__.clear()
        self.__dict__.update(deepcopy(normalized))

    def input_yaml(self, stream):
        self._input(yaml.safe_load(_text(stream)))

    def output_yaml(self):
        return yaml.safe_dump(self.__dict__, sort_keys=False, allow_unicode=True)

    def input_json(self, stream):
        self._input(json.loads(_text(stream)))

    def output_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2) + "\n"

    def _input_header(self, stream, prefix):
        text = _text(stream).replace("\r\n", "\n").replace("\r", "\n")
        lines = [
            line[len(prefix) :] for line in text.split("\n") if line.startswith(prefix)
        ]
        if not lines:
            raise ValueError(f"No {prefix} FHR metadata header found")
        self.input_yaml("\n".join(lines))

    def _output_header(self, prefix):
        lines = self.output_yaml().split("\n")
        if lines[-1] == "":
            lines.pop()
        return "".join(prefix + line + "\n" for line in lines)

    def input_fasta(self, stream):
        self._input_header(stream, ";~")

    def output_fasta(self):
        return self._output_header(";~")

    def input_gfa(self, stream):
        self._input_header(stream, "#~")

    def output_gfa(self):
        return self._output_header("#~")

    def input_microdata(self, stream):
        parser = _MetadataHTML()
        parser.feed(_text(stream))
        parser.close()
        if parser.stack or parser.result is None:
            raise ValueError("No complete FHR microdata item scope found")
        data = parser.result
        # Standard microdata scalar values are strings; restore schema-defined types.
        for key, definition in SCHEMA["properties"].items():
            if key not in data:
                continue
            if definition.get("type") == "array" and not isinstance(data[key], list):
                data[key] = [data[key]]
            if definition.get("type") in {"number", "integer"} and isinstance(
                data[key], str
            ):
                data[key] = json.loads(data[key])
        if isinstance(data.get("assemblySoftware"), dict):
            data["assemblySoftware"] = [data["assemblySoftware"]]
        if isinstance(data.get("assemblySoftware"), list):
            for software in data["assemblySoftware"]:
                if isinstance(software, dict) and isinstance(
                    software.get("commandLineOption"), str
                ):
                    software["commandLineOption"] = [software["commandLineOption"]]
        if isinstance(data.get("vitalStats"), dict):
            for key, value in data["vitalStats"].items():
                kind = (
                    SCHEMA["properties"]["vitalStats"]["properties"]
                    .get(key, {})
                    .get("type")
                )
                if kind in {"number", "integer"} and isinstance(value, str):
                    data["vitalStats"][key] = json.loads(value)
        self._input(data)

    def output_microdata(self):
        content = "".join(
            _html_value(key, value) for key, value in self.__dict__.items()
        )
        return f'<div itemscope itemtype="{ITEM_TYPE}">{content}</div>\n'

    def fhr_validate(self):
        json.dumps(self.__dict__, allow_nan=False)
        Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(
            self.__dict__
        )
