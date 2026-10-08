import re
from typing import Any

from app.domain.models import DependencyKind
from app.manifests.base import ManifestEntries, ManifestParser, load_toml, try_toml

# PEP 508 requirement: name[extras] spec ; markers   (or "name @ url" direct references)
_REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?P<rest>[^;]*?)\s*(?:;.*)?$"
)
# One or more comparison clauses: ">=1.2, <2", "==2.31.0", "~=3.1", "!=1.5.*"
_VERSION_SPEC = re.compile(r"^(?:(?:===|==|!=|~=|>=|<=|>|<)\s*[\w.*+!-]+\s*,?\s*)+$")
_REQUIREMENTS_FILENAME = re.compile(r"^(?:.*[-_.])?requirements(?:[-_.].*)?\.(?:txt|in)$|^constraints\.txt$")
# Lines that install from somewhere other than PyPI: VCS URLs, archives, local paths.
_NON_PYPI_LINE = re.compile(r"^(git\+|https?://|file:|\.{0,2}/)")
_DEV_GROUPS = {"dev", "test", "tests", "testing", "lint", "docs", "typing", "develop"}


def is_requirement(line: str) -> bool:
    """A PEP 508 requirement whose tail is a real version spec or direct reference (not prose)."""
    match = _REQUIREMENT.match(line.strip())
    if not match:
        return False
    rest = match.group("rest").strip().strip("()").strip()
    return not rest or rest.startswith("@") or bool(_VERSION_SPEC.match(rest))


def add_pep508(entries: ManifestEntries, requirement: str, kind: DependencyKind) -> None:
    requirement = requirement.strip()
    match = _REQUIREMENT.match(requirement)
    if not match:
        entries.skip(requirement[:60], "", "Unrecognised requirement")
        return
    name, rest = match.group("name"), match.group("rest").strip().strip("()").strip()
    if rest and not rest.startswith("@") and not _VERSION_SPEC.match(rest):
        entries.skip(requirement[:60], "", "Unrecognised requirement")
    elif rest.startswith("@"):
        entries.skip(name, rest, "Not installed from PyPI (direct reference)")
    else:
        entries.add(name, rest or None, kind)


class RequirementsTxtParser(ManifestParser):
    format = "requirements.txt"
    ecosystem = "pypi"
    def matches_filename(self, filename: str) -> bool:
        # requirements.txt, requirements-dev.txt, dev-requirements.txt, requirements.in, constraints.txt
        return bool(_REQUIREMENTS_FILENAME.match(filename.strip().rsplit("/", 1)[-1].lower()))

    def sniff(self, text: str) -> bool:
        lines = [re.split(r"\s+#", line, maxsplit=1)[0].strip() for line in text.splitlines()]
        lines = [line for line in lines if line and not line.startswith("#")]
        return bool(lines) and all(
            is_requirement(line.split(";")[0]) or line.startswith("-") or _NON_PYPI_LINE.match(line) for line in lines
        )

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        entries = ManifestEntries()
        for raw_line in text.splitlines():
            line = re.split(r"\s+#", raw_line, maxsplit=1)[0].strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-"):  # -r other.txt, -e ., --index-url ...
                continue
            if _NON_PYPI_LINE.match(line):
                entries.skip(line[:60], "", "Not installed from PyPI")
                continue
            add_pep508(entries, line, "prod")
        return entries


class PyprojectParser(ManifestParser):
    format = "pyproject.toml"
    ecosystem = "pypi"
    filenames = ("pyproject.toml",)

    def sniff(self, text: str) -> bool:
        data = try_toml(text)
        return bool(data) and ("project" in data or "poetry" in (data.get("tool") or {}))

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        data = load_toml(text, self.format)
        entries = ManifestEntries()
        project = data.get("project") or {}
        for requirement in project.get("dependencies") or []:
            add_pep508(entries, requirement, "prod")
        for group, requirements in (project.get("optional-dependencies") or {}).items():
            kind: DependencyKind = "dev" if group.lower() in _DEV_GROUPS else "optional"
            if kind == "dev" and not include_dev:
                continue
            for requirement in requirements:
                add_pep508(entries, requirement, kind)
        if include_dev:
            for requirements in (data.get("dependency-groups") or {}).values():  # PEP 735
                for requirement in requirements:
                    if isinstance(requirement, str):
                        add_pep508(entries, requirement, "dev")
            for requirement in ((data.get("tool") or {}).get("uv") or {}).get("dev-dependencies") or []:
                add_pep508(entries, requirement, "dev")
        self._parse_poetry(((data.get("tool") or {}).get("poetry")) or {}, entries, include_dev)
        return entries

    @staticmethod
    def _parse_poetry(poetry: dict[str, Any], entries: ManifestEntries, include_dev: bool) -> None:
        sections: list[tuple[dict[str, Any], DependencyKind]] = [(poetry.get("dependencies") or {}, "prod")]
        if include_dev:
            sections.append((poetry.get("dev-dependencies") or {}, "dev"))
            sections.extend((group.get("dependencies") or {}, "dev") for group in (poetry.get("group") or {}).values())
        for table, kind in sections:
            for name, spec in table.items():
                if name.lower() == "python":
                    continue
                add_table_spec(entries, name, spec, kind, source="PyPI")


def add_table_spec(entries: ManifestEntries, name: str, spec: Any, kind: DependencyKind, *, source: str) -> None:
    """A TOML dependency value: "1.2" or { version = "1.2" } or { git = ... } / { path = ... }."""
    if isinstance(spec, str):
        entries.add(name, None if spec.strip() == "*" else spec, kind)
    elif isinstance(spec, dict):
        if any(key in spec for key in ("git", "path", "url")):
            entries.skip(name, str(spec.get("git") or spec.get("path") or spec.get("url")), f"Not installed from {source}")
        else:
            version = spec.get("version")
            entries.add(name, None if version in (None, "*") else str(version), kind)
    elif isinstance(spec, list):  # Poetry multiple-constraint form
        entries.add(name, None, kind)


class PipfileParser(ManifestParser):
    format = "Pipfile"
    ecosystem = "pypi"
    filenames = ("pipfile",)

    def sniff(self, text: str) -> bool:
        data = try_toml(text)
        return bool(data) and ("packages" in data or "dev-packages" in data)

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        data = load_toml(text, self.format)
        entries = ManifestEntries()
        sections: list[tuple[str, DependencyKind]] = [("packages", "prod")]
        if include_dev:
            sections.append(("dev-packages", "dev"))
        for section, kind in sections:
            for name, spec in (data.get(section) or {}).items():
                add_table_spec(entries, name, spec, kind, source="PyPI")
        return entries
