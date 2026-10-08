import re

from app.domain.models import DependencyKind
from app.manifests.base import ManifestEntries, ManifestParser, load_xml

_MAVEN_PROPERTY = re.compile(r"\$\{([^}]+)\}")


class PomXmlParser(ManifestParser):
    format = "pom.xml"
    ecosystem = "maven"
    filenames = ("pom.xml",)

    def sniff(self, text: str) -> bool:
        return "<project" in text and "<artifactId>" in text

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        root = load_xml(text, self.format)
        properties = {child.tag: (child.text or "").strip() for child in root.findall("properties/*")}
        properties["project.version"] = (root.findtext("version") or root.findtext("parent/version") or "").strip()

        def resolve(value: str | None) -> str | None:
            if not value:
                return None
            resolved = _MAVEN_PROPERTY.sub(lambda m: properties.get(m.group(1), m.group(0)), value.strip())
            return None if "${" in resolved else resolved

        entries = ManifestEntries()
        for dependency in root.findall("dependencies/dependency"):
            group, artifact = dependency.findtext("groupId"), dependency.findtext("artifactId")
            if not group or not artifact:
                continue
            scope = (dependency.findtext("scope") or "compile").strip()
            kind: DependencyKind = (
                "dev" if scope == "test" else "optional" if dependency.findtext("optional") == "true" else "prod"
            )
            if kind == "dev" and not include_dev:
                continue
            entries.add(f"{resolve(group)}:{resolve(artifact)}", resolve(dependency.findtext("version")), kind)
        return entries


_GRADLE_DEPENDENCY = re.compile(
    r"""\b(?P<config>implementation|api|compileOnly|runtimeOnly|annotationProcessor|kapt|ksp|developmentOnly|"""
    r"""testImplementation|testRuntimeOnly|testCompileOnly|androidTestImplementation)\s*\(?\s*"""
    r"""["'](?P<group>[^"':\s]+):(?P<artifact>[^"':\s]+)(?::(?P<version>[^"'\s]+))?["']"""
)


class GradleParser(ManifestParser):
    format = "build.gradle"
    ecosystem = "maven"
    filenames = ("build.gradle", "build.gradle.kts")

    def sniff(self, text: str) -> bool:
        return "dependencies" in text and bool(_GRADLE_DEPENDENCY.search(text))

    def parse(self, text: str, *, include_dev: bool) -> ManifestEntries:
        entries = ManifestEntries()
        for match in _GRADLE_DEPENDENCY.finditer(text):
            kind: DependencyKind = "dev" if match.group("config").lower().startswith(("test", "androidtest")) else "prod"
            if kind == "dev" and not include_dev:
                continue
            entries.add(f"{match.group('group')}:{match.group('artifact')}", match.group("version"), kind)
        return entries
