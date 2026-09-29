""".NET manifests: SDK-style project files (.csproj/.fsproj/.vbproj) and Directory.Packages.props."""

from app.manifests.base import ManifestEntries, ManifestParser, load_xml


class CsprojParser(ManifestParser):
    format = ".csproj"
    ecosystem = "nuget"
    filenames = ("directory.packages.props",)
    suffixes = (".csproj", ".fsproj", ".vbproj")

    def sniff(self, text: str) -> bool:
        return "<Project" in text and ("<PackageReference" in text or "<PackageVersion" in text)

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        root = load_xml(text, self.format)
        entries = ManifestEntries()
        for reference in [*root.iter("PackageReference"), *root.iter("PackageVersion")]:
            name = reference.get("Include")
            if not name:
                continue  # Update="..." items modify an existing reference
            version = reference.get("Version") or reference.findtext("Version")
            # PrivateAssets="all" marks build-time tooling (analyzers, source generators).
            private = (reference.get("PrivateAssets") or reference.findtext("PrivateAssets") or "").lower() == "all"
            if private and not include_dev:
                continue
            entries.add(name, version, "dev" if private else "prod")
        return entries
