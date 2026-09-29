"""Best-effort reading of version specs across ecosystems.

Only the concrete version behind a spec matters here (to check it against OSV), so the
parser recognises the common single-clause forms and gives up on complex ranges:

    npm/composer  ^1.2.3  ~1.2.3  1.2.3        PyPI  ==1.2.3  >=1.2  ~=1.2
    Cargo         1.2.3 (= ^1.2.3)  =1.2.3     Ruby  ~> 1.2   = 1.2.3
    NuGet         1.2.3  [1.2.3]               Go    v1.2.3
"""

import re
from dataclasses import dataclass

_EXACT_OPERATORS = {"=", "==", "==="}
_SPEC_PATTERN = re.compile(
    r"^(?P<op>\^|~>|~=|~|===|==|=|>=)?\s*v?(?P<version>\d+(?:\.\d+)*(?:[-.+]?[0-9A-Za-z][0-9A-Za-z.+-]*)?)$"
)


@dataclass(frozen=True)
class VersionSpec:
    version: str | None  # the concrete version, if one can be read from the spec
    pinned: bool  # the spec allows exactly that version


def parse_version_spec(requested: str | None, *, bare_is_exact: bool) -> VersionSpec:
    if not requested:
        return VersionSpec(None, False)
    # Take the first clause of "a,b" lists; NuGet writes exact pins as "[1.2.3]".
    spec = requested.split(",")[0].strip()
    if spec.startswith("[") and spec.endswith("]"):
        spec = spec[1:-1].strip()
    match = _SPEC_PATTERN.match(spec)
    if not match:
        return VersionSpec(None, False)
    operator = match.group("op")
    pinned = operator in _EXACT_OPERATORS or (operator is None and bare_is_exact)
    return VersionSpec(match.group("version"), pinned)
