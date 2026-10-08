from app.domain.errors import InvalidInputError
from app.domain.models import DependencyKind
from app.manifests.base import ManifestEntries, ManifestParser, load_json, try_json


class ComposerJsonParser(ManifestParser):
    format = "composer.json"
    ecosystem = "packagist"
    filenames = ("composer.json",)

    def sniff(self, text: str) -> bool:
        data = try_json(text)
        if not isinstance(data, dict) or not ("require" in data or "require-dev" in data):
            return False
        names = [*(data.get("require") or {}), *(data.get("require-dev") or {})]
        return any("/" in name or name == "php" for name in names)

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        manifest = load_json(text, self.format)
        if not isinstance(manifest, dict):
            raise InvalidInputError("composer.json must be a JSON object.")
        entries = ManifestEntries()
        sections: list[tuple[str, DependencyKind]] = [("require", "prod")]
        if include_dev:
            sections.append(("require-dev", "dev"))
        for section, kind in sections:
            for name, requested in (manifest.get(section) or {}).items():
                if "/" not in name:  # "php", "ext-json", "lib-icu": platform requirements, not packages
                    continue
                entries.add(name, str(requested), kind)
        return entries
