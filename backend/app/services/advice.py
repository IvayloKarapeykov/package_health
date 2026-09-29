"""The two halves of an opinion — the verdict and its explanation — plus rule-based fallbacks.

A `VerdictDecider` picks recommended / caution / avoid; an `Explainer` then justifies that
verdict in prose and suggests alternatives. Keeping them separate lets a fast decision model
choose while a language model writes.
"""

from collections import Counter
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from app.domain.models import (
    Ecosystem,
    HealthScore,
    PackageAssessment,
    PackageSignals,
    Verdict,
    VerdictSource,
)


class AlternativeSuggestion(BaseModel):
    name: str = Field(description="Exact npm package name")
    reason: str = Field(description="One sentence on why it is a better choice")


class VerdictDecision(BaseModel):
    verdict: Verdict
    confidence: float | None = None
    source: VerdictSource


class Explanation(BaseModel):
    summary: str
    reasons: list[str]
    alternatives: list[AlternativeSuggestion] = []
    source: Literal["llm", "heuristic"]


class VerdictDecider(Protocol):
    async def decide(self, signals: PackageSignals, health: HealthScore) -> VerdictDecision: ...


class Explainer(Protocol):
    async def explain(self, signals: PackageSignals, health: HealthScore, verdict: Verdict) -> Explanation: ...

    async def summarize(self, assessments: list[PackageAssessment]) -> str: ...


# Well-known replacements for packages that are deprecated or considered legacy, per ecosystem.
KNOWN_ALTERNATIVES: dict[tuple[Ecosystem, str], list[AlternativeSuggestion]] = {
    ("npm", "request"): [
        AlternativeSuggestion(name="undici", reason="Fast, spec-compliant HTTP client maintained by the Node.js team"),
        AlternativeSuggestion(name="got", reason="Feature-rich, actively maintained HTTP client"),
        AlternativeSuggestion(name="axios", reason="Popular promise-based HTTP client for Node and browsers"),
    ],
    ("npm", "moment"): [
        AlternativeSuggestion(name="date-fns", reason="Modular, tree-shakeable date utilities"),
        AlternativeSuggestion(name="dayjs", reason="2 kB Moment-compatible API"),
        AlternativeSuggestion(name="luxon", reason="Immutable dates with first-class time zone support"),
    ],
    ("npm", "node-sass"): [AlternativeSuggestion(name="sass", reason="The official Dart Sass implementation")],
    ("npm", "tslint"): [AlternativeSuggestion(name="eslint", reason="TSLint is deprecated in favour of typescript-eslint")],
    ("npm", "left-pad"): [AlternativeSuggestion(name="string.prototype.padstart", reason="Use the native String.prototype.padStart")],
    ("npm", "querystring"): [AlternativeSuggestion(name="qs", reason="Maintained query string parser (or use URLSearchParams)")],
    ("pypi", "nose"): [AlternativeSuggestion(name="pytest", reason="The de facto Python test runner; nose is unmaintained")],
    ("pypi", "pycrypto"): [AlternativeSuggestion(name="pycryptodome", reason="Maintained drop-in fork of the abandoned PyCrypto")],
    ("packagist", "fzaninotto/faker"): [AlternativeSuggestion(name="fakerphp/faker", reason="The community-maintained continuation")],
    ("packagist", "swiftmailer/swiftmailer"): [AlternativeSuggestion(name="symfony/mailer", reason="Swift Mailer's official successor")],
}

_VERDICT_SUMMARIES = {
    Verdict.RECOMMENDED: "Healthy and actively maintained — safe to adopt.",
    Verdict.CAUTION: "Usable, but there are warning signs worth weighing first.",
    Verdict.AVOID: "Significant risks — prefer an alternative.",
    Verdict.UNKNOWN: "Could not be found on its registry.",
}


class RuleVerdictDecider:
    """Uses the rule-based baseline verdict as-is."""

    async def decide(self, signals: PackageSignals, health: HealthScore) -> VerdictDecision:
        return VerdictDecision(verdict=health.verdict, source="rules")


class HeuristicExplainer:
    """Builds an explanation straight from the rule findings; no network or LLM required."""

    async def explain(self, signals: PackageSignals, health: HealthScore, verdict: Verdict) -> Explanation:
        ordered = sorted(health.findings, key=lambda f: (f.impact != "critical", -f.penalty))
        key = (signals.dependency.ecosystem, signals.dependency.name)
        alternatives = KNOWN_ALTERNATIVES.get(key, []) if verdict != Verdict.RECOMMENDED else []
        return Explanation(
            summary=_VERDICT_SUMMARIES[verdict],
            reasons=[finding.message for finding in ordered][:5],
            alternatives=alternatives,
            source="heuristic",
        )

    async def summarize(self, assessments: list[PackageAssessment]) -> str:
        return describe_counts(assessments)


def describe_counts(assessments: list[PackageAssessment]) -> str:
    if len(assessments) == 1:
        return assessments[0].summary
    counts = Counter(assessment.verdict for assessment in assessments)
    parts = [f"{counts[Verdict.RECOMMENDED]} of {len(assessments)} dependencies look healthy"]
    if counts[Verdict.CAUTION]:
        parts.append(f"{counts[Verdict.CAUTION]} need a closer look")
    if counts[Verdict.AVOID]:
        flagged = ", ".join(a.dependency.name for a in assessments if a.verdict == Verdict.AVOID)
        parts.append(f"{counts[Verdict.AVOID]} should be replaced ({flagged})")
    if counts[Verdict.UNKNOWN]:
        parts.append(f"{counts[Verdict.UNKNOWN]} could not be found")
    return "; ".join(parts) + "."
