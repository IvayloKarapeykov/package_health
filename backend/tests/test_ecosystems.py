import httpx
import pytest
import respx

from app.core.cache import TTLCache
from app.core.http import NotFoundError
from app.ecosystems.cargo import CargoAdapter, parse_crate_document
from app.ecosystems.depsdev import DepsDevClient
from app.ecosystems.depsdev_ecosystems import GoAdapter, MavenAdapter
from app.ecosystems.npm import NpmAdapter, parse_registry_document
from app.ecosystems.packagist import PackagistAdapter, parse_packagist_package
from app.ecosystems.pypi import STATS_URL, PyPIAdapter, parse_pypi_document
from app.ecosystems.versions import parse_version_spec


def adapters(http: httpx.AsyncClient):
    cache = TTLCache(60)
    depsdev = DepsDevClient(http, cache)
    return {
        "npm": NpmAdapter(http, cache),
        "pypi": PyPIAdapter(http, cache, depsdev),
        "cargo": CargoAdapter(http, cache),
        "packagist": PackagistAdapter(http, cache),
        "go": GoAdapter(depsdev, http, cache),
        "maven": MavenAdapter(depsdev, http, cache),
    }


def test_npm_registry_document() -> None:
    document = {
        "name": "demo",
        "dist-tags": {"latest": "2.0.0"},
        "maintainers": [{"name": "a"}, {"name": "b"}],
        "time": {
            "created": "2015-01-01T00:00:00.000Z",
            "1.0.0": "2015-01-01T00:00:00.000Z",
            "2.0.0": "2020-06-01T00:00:00.000Z",
            "3.0.0-removed": "2021-01-01T00:00:00.000Z",
        },
        "versions": {
            "1.0.0": {},
            "2.0.0": {
                "license": {"type": "MIT"},
                "repository": {"type": "git", "url": "git+https://github.com/acme/demo.git"},
                "deprecated": "use demo-next",
                "dependencies": {"x": "^1"},
                "types": "index.d.ts",
            },
        },
    }
    info = parse_registry_document(document, registry_url="https://www.npmjs.com/package/demo")
    assert (info.latest_version, info.license, info.deprecated) == ("2.0.0", "MIT", "use demo-next")
    assert info.last_release_at.year == 2020  # unpublished versions are ignored
    assert (info.total_versions, info.maintainers_count, info.dependencies_count, info.has_types) == (2, 2, 1, True)


def test_npm_unpublished_package_is_not_found() -> None:
    with pytest.raises(NotFoundError):
        parse_registry_document({"time": {"unpublished": {}}}, registry_url="")


def test_pypi_document_reads_status_license_and_repository() -> None:
    document = {
        "info": {
            "version": "2.0.0",
            "summary": "Demo",
            "license": "",
            "license_expression": None,
            "classifiers": [
                "Development Status :: 7 - Inactive",
                "License :: OSI Approved :: MIT License",
                "Typing :: Typed",
            ],
            "project_urls": {"Documentation": "https://demo.readthedocs.io", "Source": "https://github.com/acme/demo"},
            "requires_dist": ["idna>=2", "pytest; extra == 'test'"],
        },
        "releases": {
            "1.0.0": [{"upload_time_iso_8601": "2019-01-01T00:00:00Z"}],
            "2.0.0": [{"upload_time_iso_8601": "2021-05-01T00:00:00Z"}],
            "2.1.0": [{"upload_time_iso_8601": "2022-01-01T00:00:00Z", "yanked": True}],
            "0.0.1": [],
        },
    }
    info = parse_pypi_document(document, registry_url="https://pypi.org/project/demo/")
    assert info.deprecated and "inactive" in info.deprecated
    assert info.license == "MIT License"
    assert info.repository_url == "https://github.com/acme/demo"
    assert (info.total_versions, info.last_release_at.year, info.dependencies_count, info.has_types) == (2, 2021, 1, True)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Django", ("Django", None)),
        ("requests>=2.31", ("requests", ">=2.31")),
        ("requests[socks] == 2.31.0", ("requests", "== 2.31.0")),
        ("requests@2.31.0", ("requests", "==2.31.0")),
    ],
)
def test_pypi_split_spec(raw: str, expected: tuple[str, str | None]) -> None:
    assert PyPIAdapter.split_spec(None, raw) == expected  # type: ignore[arg-type]


def test_pypi_names_are_normalized() -> None:
    assert PyPIAdapter.normalize_name(None, "Zope.Interface_Tools") == "zope-interface-tools"  # type: ignore[arg-type]


@respx.mock
async def test_pypi_falls_back_to_dependents_when_download_stats_are_rate_limited() -> None:
    respx.get(f"{STATS_URL}/demo/recent").mock(return_value=httpx.Response(429))
    respx.get("https://api.deps.dev/v3/systems/PYPI/packages/demo").mock(
        return_value=httpx.Response(200, json={"versions": [{"versionKey": {"version": "1.0"}, "isDefault": True}]})
    )
    respx.get("https://api.deps.dev/v3/systems/PYPI/packages/demo/versions/1.0").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(url__regex=r".*:dependents$").mock(return_value=httpx.Response(200, json={"dependentCount": 42}))
    async with httpx.AsyncClient() as http:
        adoption = await adapters(http)["pypi"].get_adoption("demo")
    assert (adoption.weekly_downloads, adoption.dependents) == (None, 42)


def test_crate_document_ignores_yanked_versions() -> None:
    document = {
        "crate": {"default_version": "1.1.0", "description": "Demo", "repository": "https://github.com/acme/demo"},
        "versions": [
            {"num": "1.2.0", "created_at": "2024-01-01T00:00:00Z", "yanked": True, "license": "MIT"},
            {"num": "1.1.0", "created_at": "2023-01-01T00:00:00Z", "yanked": False, "license": "MIT OR Apache-2.0"},
        ],
    }
    info = parse_crate_document(document, registry_url="")
    assert (info.latest_version, info.license, info.total_versions, info.deprecated) == ("1.1.0", "MIT OR Apache-2.0", 1, None)


@pytest.mark.parametrize(
    ("abandoned", "expected"),
    [(None, None), (True, "Abandoned by its maintainers"), ("fakerphp/faker", "suggest fakerphp/faker")],
)
def test_packagist_abandoned_packages_are_deprecated(abandoned, expected) -> None:
    package = {
        "abandoned": abandoned,
        "versions": {
            "dev-main": {"time": "2024-06-01T00:00:00+00:00"},
            "v1.9.2": {"time": "2020-12-11T00:00:00+00:00", "license": ["MIT"]},
            "1.9.1": {"time": "2019-12-12T00:00:00+00:00", "license": ["MIT"]},
        },
    }
    info = parse_packagist_package(package, registry_url="")
    assert (info.latest_version, info.total_versions, info.license) == ("1.9.2", 2, "MIT")
    if expected is None:
        assert info.deprecated is None
    else:
        assert expected in (info.deprecated or "")


@pytest.mark.parametrize(
    ("ecosystem", "name", "valid"),
    [
        ("npm", "@babel/core", True),
        ("npm", "Not Valid!", False),
        ("pypi", "zope-interface", True),
        ("cargo", "serde_json", True),
        ("packagist", "laravel/framework", True),
        ("packagist", "laravel", False),
        ("go", "github.com/gin-gonic/gin", True),
        ("go", "gin", False),
        ("maven", "com.google.guava:guava", True),
        ("maven", "guava", False),
    ],
)
async def test_name_validation(ecosystem: str, name: str, valid: bool) -> None:
    async with httpx.AsyncClient() as http:
        assert adapters(http)[ecosystem].is_valid_name(name) is valid


@pytest.mark.parametrize(
    ("ecosystem", "raw", "expected"),
    [
        ("npm", "@babel/core@^7.0.0", ("@babel/core", "^7.0.0")),
        ("maven", "org.slf4j:slf4j-api:2.0.9", ("org.slf4j:slf4j-api", "2.0.9")),
        ("packagist", "laravel/framework:^10.0", ("laravel/framework", "^10.0")),
        ("go", "github.com/gin-gonic/gin@v1.9.1", ("github.com/gin-gonic/gin", "v1.9.1")),
    ],
)
async def test_split_spec(ecosystem: str, raw: str, expected: tuple[str, str | None]) -> None:
    async with httpx.AsyncClient() as http:
        assert adapters(http)[ecosystem].split_spec(raw) == expected


@pytest.mark.parametrize(
    ("spec", "bare_is_exact", "version", "pinned"),
    [
        ("1.2.3", True, "1.2.3", True),
        ("1.2.3", False, "1.2.3", False),  # Cargo: bare means ^1.2.3
        ("^1.2.3", True, "1.2.3", False),
        ("==2.31.0", True, "2.31.0", True),
        (">=2.0,<3", True, "2.0", False),
        ("~> 7.0", True, "7.0", False),
        ("= 1.2.3", True, "1.2.3", True),
        ("[12.0.1]", True, "12.0.1", True),
        ("v1.9.1", True, "1.9.1", True),
        ("33.7.1-jre", True, "33.7.1-jre", True),
        ("^1.2 || ^2", True, None, False),
        ("*", True, None, False),
        (None, True, None, False),
    ],
)
def test_version_specs(spec: str | None, bare_is_exact: bool, version: str | None, pinned: bool) -> None:
    parsed = parse_version_spec(spec, bare_is_exact=bare_is_exact)
    assert (parsed.version, parsed.pinned) == (version, pinned)
