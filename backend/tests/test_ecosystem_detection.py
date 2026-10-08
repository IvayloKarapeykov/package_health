import httpx
import pytest

from app.container import build_ecosystems
from app.core.cache import TTLCache
from app.core.http import UpstreamError
from app.domain.errors import InvalidInputError
from app.domain.models import Adoption
from app.services.ecosystem_detection import EcosystemDetector


@pytest.fixture
async def registry():
    async with httpx.AsyncClient() as http:
        yield build_ecosystems(http, TTLCache(60))


def publish(registry, packages: dict[str, Adoption | Exception]) -> list[str]:
    """Fake every registry: `packages` maps ecosystem -> the adoption it reports (or the error it raises).

    Returns the log of registries that were probed.
    """
    probed: list[str] = []
    for adapter in registry.all():

        async def exists(name: str, ecosystem=adapter.id) -> bool:
            probed.append(ecosystem)
            found = packages.get(ecosystem)
            if isinstance(found, Exception):
                raise found
            return found is not None

        async def get_adoption(name: str, ecosystem=adapter.id) -> Adoption:
            found = packages[ecosystem]
            assert isinstance(found, Adoption)  # exists() already raised for errors
            return found

        adapter.exists = exists
        adapter.get_adoption = get_adoption
    return probed


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("@tanstack/react-query", "npm"),
        ("org.slf4j:slf4j-api:2.0.9", "maven"),
        ("laravel/framework", "packagist"),
        ("github.com/gin-gonic/gin", "go"),
        ("django>=4.2", "pypi"),
    ],
)
async def test_syntax_alone_decides_without_network(registry, raw, expected) -> None:
    probed = publish(registry, {})
    detection = await EcosystemDetector(registry).detect(raw)
    assert (detection.ecosystem, detection.also_found_in, probed) == (expected, [], [])


async def test_most_used_registry_wins_across_different_measures(registry) -> None:
    publish(
        registry,
        {
            "npm": Adoption(weekly_downloads=40_000),
            "pypi": Adoption(weekly_downloads=120_000_000),
            "rubygems": Adoption(total_downloads=300_000),
        },
    )
    detection = await EcosystemDetector(registry).detect("requests")
    assert (detection.ecosystem, detection.also_found_in) == ("pypi", ["npm", "rubygems"])


async def test_unreachable_registries_are_skipped(registry) -> None:
    publish(registry, {"npm": UpstreamError("registry", "timeout"), "cargo": Adoption(weekly_downloads=10)})
    detection = await EcosystemDetector(registry).detect("serde")
    assert (detection.ecosystem, detection.also_found_in) == ("cargo", [])


async def test_equally_used_packages_prefer_the_bigger_ecosystem(registry) -> None:
    publish(registry, {"rubygems": Adoption(), "npm": Adoption()})
    assert (await EcosystemDetector(registry).detect("left-pad")).ecosystem == "npm"


@pytest.mark.parametrize("raw", ["Not Valid!", "no-such-package-anywhere"])
async def test_unknown_or_malformed_names_are_invalid_input(registry, raw) -> None:
    publish(registry, {})
    with pytest.raises(InvalidInputError):
        await EcosystemDetector(registry).detect(raw)
