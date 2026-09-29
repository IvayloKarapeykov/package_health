"""Rust manifests: Cargo.toml (dependencies, dev/build dependencies, workspaces, targets)."""

from typing import Any

from app.domain.models import DependencyKind
from app.manifests.base import ManifestEntries, ManifestParser, load_toml, try_toml
from app.manifests.python import add_table_spec


class CargoTomlParser(ManifestParser):
    format = "Cargo.toml"
    ecosystem = "cargo"
    filenames = ("cargo.toml",)

    def sniff(self, text: str) -> bool:
        data = try_toml(text)
        return bool(data) and ("package" in data or "workspace" in data) and "project" not in data

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        data = load_toml(text, self.format)
        tables: list[tuple[dict[str, Any], DependencyKind]] = [
            (data.get("dependencies") or {}, "prod"),
            ((data.get("workspace") or {}).get("dependencies") or {}, "prod"),
        ]
        tables.extend((target.get("dependencies") or {}, "prod") for target in (data.get("target") or {}).values())
        if include_dev:
            tables.extend([(data.get("dev-dependencies") or {}, "dev"), (data.get("build-dependencies") or {}, "dev")])

        entries = ManifestEntries()
        for table, kind in tables:
            for name, spec in table.items():
                if isinstance(spec, dict) and spec.get("workspace"):
                    entries.add(spec.get("package", name), None, kind)  # version lives in the workspace root
                    continue
                crate = spec.get("package", name) if isinstance(spec, dict) else name  # renamed dependency
                add_table_spec(entries, crate, spec, kind, source="crates.io")
        return entries
