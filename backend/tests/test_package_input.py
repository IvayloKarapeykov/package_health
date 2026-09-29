import json

import httpx
import pytest

from app.container import build_ecosystems
from app.core.cache import TTLCache
from app.domain.errors import InvalidInputError
from app.services.package_input import DependencyInputParser


@pytest.fixture
async def parser():
    async with httpx.AsyncClient() as http:
        yield DependencyInputParser(build_ecosystems(http, TTLCache(60)), max_packages=3)


@pytest.mark.parametrize(
    ("raw", "ecosystem", "name", "requested"),
    [
        ("  Express ", "npm", "express", None),
        ("@babel/core@^7.0.0", "npm", "@babel/core", "^7.0.0"),
        ("Django>=4.2", "pypi", "django", ">=4.2"),
        ("org.slf4j:slf4j-api:2.0.9", "maven", "org.slf4j:slf4j-api", "2.0.9"),
    ],
)
async def test_parse_package(parser, raw, ecosystem, name, requested) -> None:
    [dependency] = parser.parse_package(raw, ecosystem).dependencies
    assert (dependency.name, dependency.ecosystem, dependency.requested, dependency.kind) == (name, ecosystem, requested, "direct")


@pytest.mark.parametrize(("raw", "ecosystem"), [("Not Valid!", "npm"), ("Not Valid!", "pypi"), ("guava", "maven"), ("laravel", "packagist")])
async def test_parse_package_rejects_invalid_names(parser, raw, ecosystem) -> None:
    with pytest.raises(InvalidInputError):
        parser.parse_package(raw, ecosystem)


async def test_manifest_names_are_normalized_deduplicated_and_limited(parser) -> None:
    parsed = parser.parse_manifest("Flask\nflask==3.0\nrequests\nhttpx\nrich\n", filename=None, include_dev=True)

    assert (parsed.ecosystem, parsed.manifest) == ("pypi", "requirements.txt")
    assert [d.name for d in parsed.dependencies] == ["flask", "requests", "httpx"]
    assert [(s.name, s.reason) for s in parsed.skipped] == [("rich", "Analysis limit of 3 packages reached")]


async def test_manifest_with_no_dependencies_is_rejected(parser) -> None:
    with pytest.raises(InvalidInputError):
        parser.parse_manifest(json.dumps({"name": "x", "dependencies": {}}), filename="package.json", include_dev=True)
