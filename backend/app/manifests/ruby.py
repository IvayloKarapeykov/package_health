import re

from app.manifests.base import ManifestEntries, ManifestParser

_GEM_LINE = re.compile(r"""^gem\s+["'](?P<name>[^"']+)["'](?P<args>.*)$""")
_GEM_VERSION = re.compile(r"""["'](?P<spec>(?:[~<>=!]+\s*)?\d[^"']*)["']""")
_GEM_GROUP = re.compile(r"^group\s+(?P<groups>.+?)\s+do\b")
_DEV_GEM_GROUPS = {"development", "test"}


class GemfileParser(ManifestParser):
    format = "Gemfile"
    ecosystem = "rubygems"
    filenames = ("gemfile",)

    def sniff(self, text: str) -> bool:
        return bool(re.search(r"""^\s*gem\s+["']""", text, re.MULTILINE))

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        entries = ManifestEntries()
        group_stack: list[bool] = []  # is each open `do` block a dev group?
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if group := _GEM_GROUP.match(line):
                groups = set(re.findall(r":(\w+)", group.group("groups")))
                group_stack.append(bool(groups) and groups <= _DEV_GEM_GROUPS)
                continue
            if re.search(r"\bdo\b(\s*\|.*\|)?$", line):
                group_stack.append(False)  # platforms/source/etc blocks
                continue
            if line == "end" and group_stack:
                group_stack.pop()
                continue
            gem = _GEM_LINE.match(line)
            if not gem:
                continue
            args = gem.group("args")
            inline_groups = set(re.findall(r":(\w+)", (re.search(r"groups?:\s*(\[.*?\]|:\w+)", args) or [""])[0]))
            dev = any(group_stack) or (bool(inline_groups) and inline_groups <= _DEV_GEM_GROUPS)
            if dev and not include_dev:
                continue
            if re.search(r"\b(git|github|path):", args):
                entries.skip(gem.group("name"), "", "Not installed from RubyGems")
                continue
            version = _GEM_VERSION.search(args)
            entries.add(gem.group("name"), version.group("spec") if version else None, "dev" if dev else "prod")
        return entries
