import re
from typing import Any

import yaml

from app.domain.errors import InvalidInputError
from app.domain.models import DependencyKind
from app.manifests.base import ManifestEntries, ManifestParser, load_json, try_json

# Order matters: the first section a package appears in determines its kind.
_SECTIONS: tuple[tuple[str, DependencyKind], ...] = (
    ("dependencies", "prod"),
    ("peerDependencies", "peer"),
    ("optionalDependencies", "optional"),
    ("devDependencies", "dev"),
)
_NON_REGISTRY_PREFIXES = ("file:", "link:", "workspace:", "git", "http:", "https:", "portal:")
_NPM_ALIAS_PREFIX = "npm:"
_PNPM_PEER_SUFFIX = re.compile(r"\(.*\)$")  # "18.2.0(react@18.2.0)" -> "18.2.0"


def _add_npm_entry(entries: ManifestEntries, name: str, requested: str, kind: DependencyKind) -> None:
    if requested.startswith(_NPM_ALIAS_PREFIX):
        # "string-width-cjs": "npm:string-width@^4.2.0" installs string-width.
        target = requested.removeprefix(_NPM_ALIAS_PREFIX)
        at = target.find("@", 1)
        target_name, target_version = (target[:at], target[at + 1 :]) if at > 0 else (target, None)
        entries.add(target_name, target_version, kind)
    elif requested.startswith(_NON_REGISTRY_PREFIXES) or "/" in requested:
        # Version ranges never contain "/", so "user/repo" style specs point at GitHub.
        entries.skip(name, requested, "Not installed from the npm registry")
    else:
        entries.add(name, requested, kind)


class PackageJsonParser(ManifestParser):
    format = "package.json"
    ecosystem = "npm"
    filenames = ("package.json",)

    def sniff(self, text: str) -> bool:
        data = try_json(text)
        return (
            isinstance(data, dict)
            and "lockfileVersion" not in data
            and any(section in data for section, _ in _SECTIONS)
        )

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        manifest = load_json(text, self.format)
        if not isinstance(manifest, dict):
            raise InvalidInputError("package.json must be a JSON object.")
        entries = ManifestEntries()
        for section, kind in _SECTIONS:
            if kind == "dev" and not include_dev:
                continue
            values = manifest.get(section) or {}
            if not isinstance(values, dict):
                raise InvalidInputError(f"'{section}' must be an object of name → version.")
            for name, requested in values.items():
                _add_npm_entry(entries, name, str(requested), kind)
        return entries


class PackageLockParser(ManifestParser):
    format = "package-lock.json"
    ecosystem = "npm"
    filenames = ("package-lock.json", "npm-shrinkwrap.json")

    def sniff(self, text: str) -> bool:
        data = try_json(text)
        return isinstance(data, dict) and "lockfileVersion" in data and "packages" in data

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        lock = load_json(text, self.format)
        packages: dict[str, Any] = lock.get("packages") or {}
        if "" not in packages:
            raise InvalidInputError("Only lockfileVersion 2 and 3 are supported; paste package.json instead.")
        root = packages[""]
        entries = ManifestEntries()
        for section, kind in _SECTIONS:
            if kind == "dev" and not include_dev:
                continue
            for name, requested in (root.get(section) or {}).items():
                installed = (packages.get(f"node_modules/{name}") or {}).get("version")
                _add_npm_entry(entries, name, installed or str(requested), kind)
        return entries


class PnpmLockParser(ManifestParser):
    format = "pnpm-lock.yaml"
    ecosystem = "npm"
    filenames = ("pnpm-lock.yaml",)

    def sniff(self, text: str) -> bool:
        return text.lstrip().startswith("lockfileVersion:")

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        try:
            lock = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise InvalidInputError(f"pnpm-lock.yaml is not valid YAML: {exc}.") from exc
        if not isinstance(lock, dict):
            raise InvalidInputError("pnpm-lock.yaml must be a YAML mapping.")
        # pnpm v6+ keeps the root project's direct dependencies under importers["."];
        # older lockfiles keep them at the top level.
        root = (lock.get("importers") or {}).get(".") or lock
        entries = ManifestEntries()
        sections: tuple[tuple[str, DependencyKind], ...] = (
            ("dependencies", "prod"),
            ("optionalDependencies", "optional"),
            ("devDependencies", "dev"),
        )
        for section, kind in sections:
            if kind == "dev" and not include_dev:
                continue
            for name, spec in (root.get(section) or {}).items():
                version = spec.get("version") if isinstance(spec, dict) else spec
                version = _PNPM_PEER_SUFFIX.sub("", str(version or ""))
                if version.startswith(("link:", "file:")):
                    entries.skip(name, version, "Not installed from the npm registry")
                else:
                    entries.add(name, version, kind)
        return entries
