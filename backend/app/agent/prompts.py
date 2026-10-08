import json
from typing import Any

from app.core.time import days_since, utc_now
from app.domain.ecosystems import ECOSYSTEMS
from app.domain.models import Adoption, HealthScore, PackageAssessment, PackageSignals, Verdict

VERDICT_INSTRUCTIONS = "Should a software team adopt this package as a new dependency today?"

VERDICT_CRITERIA = {
    "recommended": (
        "Healthy and maintained: released or committed to within the last year, meaningful adoption, "
        "and no high or critical vulnerabilities affecting the latest version."
    ),
    "caution": (
        "Usable but with risks worth weighing first: no release for over a year, a small community or "
        "low adoption, or moderate/low vulnerabilities affecting the latest version."
    ),
    "avoid": (
        "Should not be adopted: deprecated, archived, abandoned for several years, or the latest version "
        "has high or critical vulnerabilities."
    ),
}


def build_verdict_state(signals: PackageSignals, health: HealthScore) -> dict[str, str]:
    """Facts for Jev, pre-interpreted into plain language.

    Jev is documented as unreliable at date comparison and arithmetic, and loses accuracy on
    irrelevant detail, so it gets relative phrases ("3 years ago") and only decision-relevant facts.
    It does not see the rule-based verdict, so its decision stays independent.
    """
    now = utc_now()
    registry, adoption, repository, vulns = (
        signals.registry,
        signals.adoption,
        signals.repository,
        signals.vulnerabilities,
    )
    state = {
        "package": signals.dependency.name,
        "ecosystem": ECOSYSTEMS[signals.dependency.ecosystem].description,
    }
    if registry:
        state["description"] = registry.description or "none"
        state["registry_status"] = f"deprecated: {registry.deprecated}" if registry.deprecated else "not deprecated"
        state["release_activity"] = (
            f"last release {_ago(days_since(registry.last_release_at, now))}; "
            f"{registry.releases_last_year} releases in the last 12 months"
        )
        state["license"] = registry.license or "none declared"
    if adoption and (described := describe_adoption(adoption)):
        state["adoption"] = described
    if repository:
        state["github"] = (
            f"{repository.stars:,} stars; last commit {_ago(days_since(repository.last_commit_at, now))}; "
            f"{'archived (read-only)' if repository.archived else 'not archived'}"
        )
    if vulns:
        affecting = vulns.affecting_latest
        state["vulnerabilities_in_latest_version"] = (
            ", ".join(f"{v.severity.value} ({v.id})" for v in affecting) if affecting else "none"
        )
    state["health_checks"] = "; ".join(finding.message for finding in health.findings) or "none"
    if signals.issues:
        state["unavailable_data"] = "; ".join(f"{issue.source}: {issue.message}" for issue in signals.issues)
    return state


def describe_adoption(adoption: Adoption) -> str | None:
    parts = []
    if adoption.weekly_downloads is not None:
        parts.append(f"{adoption.weekly_downloads:,} downloads per week")
    if adoption.total_downloads is not None:
        parts.append(f"{adoption.total_downloads:,} downloads all-time")
    if adoption.dependents is not None:
        parts.append(f"{adoption.dependents:,} dependent packages")
    return "; ".join(parts) or None


def _ago(days: int | None) -> str:
    if days is None:
        return "unknown"
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{round(days / 7)} weeks ago"
    if days < 365:
        return f"{round(days / 30)} months ago"
    years = round(days / 365)
    return f"{years} year{'s' if years != 1 else ''} ago"


EXPLAIN_SYSTEM_PROMPT = """\
You are a senior software engineer explaining to a team why a package received its verdict. The \
package's ecosystem (npm, PyPI, Maven, ...) is given as `ecosystem`.

The verdict ("recommended", "caution" or "avoid") has already been decided and is given as \
`verdict`. Do not change or contradict it; explain it. You also receive facts collected moments \
ago from its package registry, GitHub and OSV.dev, plus rule-based findings.

Rules:
- Ground every reason in the provided data. Cite concrete numbers (downloads, dates, counts). \
Never invent statistics.
- If some facts pull against the verdict (e.g. huge adoption but deprecated), acknowledge the \
tension honestly while explaining why the verdict still holds.
- Missing data (e.g. GitHub rate limited) should be mentioned, not guessed.
- Suggest up to 3 alternatives that are real, currently maintained packages from the same \
ecosystem, using that registry's exact package names (e.g. "group:artifact" on Maven, \
"vendor/package" on Packagist, a module path in Go). Only when the verdict is "caution" or \
"avoid", or when a clearly superior modern option exists. If the language's standard library \
covers the need, say so in a reason instead. Otherwise return an empty list.
- Write naturally for the team. The verdict is shown next to your text, so never refer to \
"the verdict", quote its label, or say the package "earns" it; just state what matters.
- summary: one or two plain sentences. reasons: 2-5 short bullet-style sentences."""

SUMMARY_SYSTEM_PROMPT = """\
You are a senior software engineer summarizing a dependency health audit of a project's \
dependency file for the team that owns it. Write 2-4 plain sentences (no markdown, no bullet points): the \
overall health, the most urgent problems by package name, and the single most valuable next \
step. Only use the facts provided."""


def build_explanation_input(signals: PackageSignals, health: HealthScore, verdict: Verdict) -> str:
    return json.dumps(_signals_digest(signals, health, verdict), indent=2, default=str)


def build_summary_input(assessments: list[PackageAssessment]) -> str:
    rows = [
        {
            "package": a.dependency.name,
            "ecosystem": ECOSYSTEMS[a.dependency.ecosystem].label,
            "kind": a.dependency.kind,
            "verdict": a.verdict.value,
            "score": a.score,
            "summary": a.summary,
            "alternatives": [alt.name for alt in a.alternatives],
        }
        for a in assessments
    ]
    return json.dumps(rows, indent=2)


def _signals_digest(signals: PackageSignals, health: HealthScore, verdict: Verdict) -> dict[str, Any]:
    now = utc_now()
    registry, adoption, repository, vulns = (
        signals.registry,
        signals.adoption,
        signals.repository,
        signals.vulnerabilities,
    )
    return {
        "package": signals.dependency.name,
        "ecosystem": ECOSYSTEMS[signals.dependency.ecosystem].description,
        "verdict": verdict.value,
        "requested_version": signals.dependency.requested,
        "registry": registry
        and {
            "latest_version": registry.latest_version,
            "description": registry.description or (repository and repository.description),
            "license": registry.license,
            "deprecated": registry.deprecated,
            "days_since_last_release": days_since(registry.last_release_at, now),
            "package_age_days": days_since(registry.created_at, now),
            "total_versions": registry.total_versions,
            "releases_last_12_months": registry.releases_last_year,
            "maintainers": registry.maintainers_count,
            "direct_dependencies": registry.dependencies_count,
            "unpacked_size_kb": registry.unpacked_size_bytes and registry.unpacked_size_bytes // 1024,
            "ships_type_information": registry.has_types,
        },
        "adoption": adoption and adoption.model_dump(exclude_none=True),
        "github": repository
        and {
            "repo": repository.full_name,
            "stars": repository.stars,
            "forks": repository.forks,
            "open_issues_and_prs": repository.open_issues,
            "archived": repository.archived,
            "days_since_last_commit": days_since(repository.last_commit_at, now),
        },
        "vulnerabilities": vulns
        and {
            "total_known_all_versions": vulns.total_known,
            "affecting_latest": [
                {"id": v.id, "severity": v.severity.value, "summary": v.summary}
                for v in vulns.affecting_latest
            ],
            "affecting_requested_version": len(vulns.affecting_requested),
        },
        "unavailable_data": [f"{issue.source}: {issue.message}" for issue in signals.issues],
        "rule_findings": {
            "score": health.score,
            "findings": [finding.message for finding in health.findings],
        },
    }
