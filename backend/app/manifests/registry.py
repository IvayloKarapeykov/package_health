"""Picks the right manifest parser from a file name or, failing that, from the content itself."""

from app.domain.errors import InvalidInputError
from app.manifests.base import ManifestParser
from app.manifests.dotnet import CsprojParser
from app.manifests.golang import GoModParser
from app.manifests.jvm import GradleParser, PomXmlParser
from app.manifests.npm import PackageJsonParser, PackageLockParser, PnpmLockParser
from app.manifests.php import ComposerJsonParser
from app.manifests.python import PipfileParser, PyprojectParser, RequirementsTxtParser
from app.manifests.ruby import GemfileParser
from app.manifests.rust import CargoTomlParser

# Most specific formats first: content sniffing stops at the first match, and
# requirements.txt (a loose line-based format) must come last.
MANIFEST_PARSERS: tuple[ManifestParser, ...] = (
    PackageLockParser(),
    PnpmLockParser(),
    ComposerJsonParser(),
    PackageJsonParser(),
    PomXmlParser(),
    CsprojParser(),
    CargoTomlParser(),
    PyprojectParser(),
    PipfileParser(),
    GoModParser(),
    GradleParser(),
    GemfileParser(),
    RequirementsTxtParser(),
)

SUPPORTED_FORMATS = ", ".join(parser.format for parser in MANIFEST_PARSERS)


def find_parser(text: str, filename: str | None = None) -> ManifestParser:
    if filename:
        parser = next((p for p in MANIFEST_PARSERS if p.matches_filename(filename)), None)
        if parser is None:
            raise InvalidInputError(f"'{filename}' isn't a supported file. Supported: {SUPPORTED_FORMATS}.")
        return parser
    parser = next((p for p in MANIFEST_PARSERS if p.sniff(text)), None)
    if parser is None:
        raise InvalidInputError(f"Couldn't recognise this file. Supported: {SUPPORTED_FORMATS}.")
    return parser
