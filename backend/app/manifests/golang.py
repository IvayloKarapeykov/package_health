import re

from app.manifests.base import ManifestEntries, ManifestParser

_GO_REQUIRE_LINE = re.compile(r"^(?P<module>\S+)\s+(?P<version>v\S+)(?P<comment>\s*//.*)?$")


class GoModParser(ManifestParser):
    format = "go.mod"
    ecosystem = "go"
    filenames = ("go.mod",)

    def sniff(self, text: str) -> bool:
        return bool(re.search(r"^module\s+\S+", text, re.MULTILINE))

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        entries = ManifestEntries()
        in_block = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("require ("):
                in_block = True
                continue
            if in_block and line == ")":
                in_block = False
                continue
            if line.startswith("require "):
                line = line.removeprefix("require ").strip()
            elif not in_block:
                continue
            match = _GO_REQUIRE_LINE.match(line)
            # Indirect requirements are transitive; only direct dependencies are the project's choice.
            if match and "indirect" not in (match.group("comment") or ""):
                entries.add(match.group("module"), match.group("version"), "prod")
        return entries
