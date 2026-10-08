import re
from urllib.parse import quote

from app.domain.models import Adoption
from app.ecosystems.depsdev import DepsDevAdapter


class GoAdapter(DepsDevAdapter):
    id = "go"
    osv_ecosystem = "Go"
    system = "GO"
    # A module path: a domain, then path elements (github.com/gin-gonic/gin, golang.org/x/net/v2)
    name_pattern = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}(/[A-Za-z0-9._~-]+)+$")

    def package_url(self, name: str) -> str:
        return f"https://pkg.go.dev/{name}"

    async def get_adoption(self, name: str) -> Adoption:
        # The Go module proxy publishes no download counts; GitHub activity carries the signal.
        return Adoption(note="Go modules publish no download counts")


class MavenAdapter(DepsDevAdapter):
    id = "maven"
    osv_ecosystem = "Maven"
    system = "MAVEN"
    name_pattern = re.compile(r"^[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+$")

    def split_spec(self, raw: str) -> tuple[str, str | None]:
        # Maven coordinates: group:artifact[:version]
        parts = raw.strip().split(":")
        if len(parts) >= 3:
            return ":".join(parts[:2]), parts[2] or None
        return raw.strip(), None

    def package_url(self, name: str) -> str:
        group, _, artifact = name.partition(":")
        return f"https://central.sonatype.com/artifact/{group}/{artifact}"

    async def get_adoption(self, name: str) -> Adoption:
        package = await self._depsdev.package(self.system, name)
        dependents = await self._depsdev.dependents(self.system, name, package.default_version)
        return Adoption(dependents=dependents, note="packages on Maven Central that depend on it")


class NuGetAdapter(DepsDevAdapter):
    id = "nuget"
    osv_ecosystem = "NuGet"
    system = "NUGET"
    name_pattern = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

    def package_url(self, name: str) -> str:
        return f"https://www.nuget.org/packages/{name}"

    async def description(self, name: str) -> str | None:
        return (await self._search(name) or {}).get("description")

    async def get_adoption(self, name: str) -> Adoption:
        found = await self._search(name)
        return Adoption(total_downloads=found.get("totalDownloads") if found else None, note="all-time downloads")

    async def _search(self, name: str) -> dict | None:
        payload = await self._extra(
            "https://azuresearch-usnc.nuget.org/query", q=f"packageid:{name}", prerelease="false", semVerLevel="2.0.0"
        )
        hits = (payload or {}).get("data") or []
        return next((hit for hit in hits if hit.get("id", "").lower() == name.lower()), None)


class RubyGemsAdapter(DepsDevAdapter):
    id = "rubygems"
    osv_ecosystem = "RubyGems"
    system = "RUBYGEMS"
    name_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

    def package_url(self, name: str) -> str:
        return f"https://rubygems.org/gems/{name}"

    async def description(self, name: str) -> str | None:
        return (await self._gem(name) or {}).get("info")

    async def get_adoption(self, name: str) -> Adoption:
        gem = await self._gem(name)
        return Adoption(total_downloads=gem.get("downloads") if gem else None, note="all-time downloads")

    async def _gem(self, name: str) -> dict | None:
        return await self._extra(f"https://rubygems.org/api/v1/gems/{quote(name, safe='')}.json")
