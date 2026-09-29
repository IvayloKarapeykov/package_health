"""What the user asks the advisor to analyze."""

from typing import Annotated, Literal

from pydantic import Field

from app.domain.models import CamelModel, Ecosystem

AUTO_DETECT = "auto"
EcosystemChoice = Ecosystem | Literal["auto"]


class PackageRequest(CamelModel):
    mode: Literal["package"] = "package"
    # "auto" looks the name up in every registry whose naming rules it fits and picks the most used.
    ecosystem: EcosystemChoice = AUTO_DETECT
    package: str = Field(min_length=1, max_length=256, examples=["express", "requests>=2.31", "org.slf4j:slf4j-api"])


class ManifestRequest(CamelModel):
    """A dependency file: package.json, requirements.txt, pyproject.toml, go.mod, pom.xml, ..."""

    mode: Literal["manifest"] = "manifest"
    content: str = Field(min_length=2, max_length=500_000)
    # Optional hint; when omitted the format is detected from the content.
    filename: str | None = Field(default=None, max_length=256)
    include_dev: bool = True


AnalysisRequest = Annotated[PackageRequest | ManifestRequest, Field(discriminator="mode")]
