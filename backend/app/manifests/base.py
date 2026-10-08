"""Parsers only extract raw entries. Normalization, validation and limits happen in
`app.services.package_input`, using the ecosystem's adapter."""

import json
import tomllib
import xml.etree.ElementTree as ElementTree
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.domain.errors import InvalidInputError
from app.domain.models import DependencyKind, Ecosystem


@dataclass(frozen=True)
class RawDependency:
    name: str
    requested: str | None
    kind: DependencyKind


@dataclass(frozen=True)
class RawSkip:
    name: str
    requested: str
    reason: str


@dataclass
class ManifestEntries:
    dependencies: list[RawDependency] = field(default_factory=list)
    skipped: list[RawSkip] = field(default_factory=list)

    def add(self, name: str, requested: str | None, kind: DependencyKind) -> None:
        self.dependencies.append(RawDependency(name.strip(), (requested or "").strip() or None, kind))

    def skip(self, name: str, requested: str | None, reason: str) -> None:
        self.skipped.append(RawSkip(name.strip(), (requested or "").strip(), reason))


class ManifestParser(ABC):
    format: str  # the canonical file name shown to users, e.g. "pyproject.toml"
    ecosystem: Ecosystem
    filenames: tuple[str, ...] = ()  # exact file names this parser handles
    suffixes: tuple[str, ...] = ()  # or file name endings, e.g. ".csproj"

    def matches_filename(self, filename: str) -> bool:
        base = filename.strip().rsplit("/", 1)[-1].lower()
        return base in self.filenames or base.endswith(self.suffixes)

    @abstractmethod
    def sniff(self, text: str) -> bool:
        """Cheaply decide whether `text` looks like this format (used when no file name is given)."""

    @abstractmethod
    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        """Extract dependencies. Raises InvalidInputError if the file can't be read."""


def load_json(text: str, file: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidInputError(f"{file} is not valid JSON: {exc.msg} (line {exc.lineno}).") from exc


def load_toml(text: str, file: str) -> dict[str, Any]:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise InvalidInputError(f"{file} is not valid TOML: {exc}.") from exc


def load_xml(text: str, file: str) -> ElementTree.Element:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise InvalidInputError(f"{file} is not valid XML: {exc}.") from exc
    for element in root.iter():  # drop namespaces so paths stay readable: {ns}dependency -> dependency
        element.tag = element.tag.rsplit("}", 1)[-1]
    return root


def try_json(text: str) -> Any | None:
    try:
        return json.loads(text)
    except ValueError:
        return None


def try_toml(text: str) -> dict[str, Any] | None:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
