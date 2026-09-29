// Mirrors the backend domain models (app/domain/*.py), serialized with camelCase keys.

export type Verdict = "recommended" | "caution" | "avoid" | "unknown"
export type Severity = "critical" | "high" | "moderate" | "low" | "unknown"
export type Ecosystem = "npm" | "pypi" | "cargo" | "go" | "maven" | "nuget" | "rubygems" | "packagist"
/** What the user picks for a single package: a registry, or "auto" to let the backend detect it. */
export type EcosystemChoice = Ecosystem | "auto"
export type DependencyKind = "direct" | "prod" | "dev" | "peer" | "optional"
export type DataSource = "registry" | "adoption" | "github" | "osv" | "llm"
/** The steps one package's analysis walks through, in order. */
export type AssessmentStep = "registry" | "activity" | "scoring" | "deciding" | "explaining" | "alternatives"
/** Who picked the verdict: the Jev decision model, or the rule-based scorer. */
export type VerdictSource = "jev" | "rules"

export interface DependencyRef {
  name: string
  ecosystem: Ecosystem
  requested: string | null
  kind: DependencyKind
}

/** Unique across ecosystems; matches the backend's `DependencyRef.key`. */
export function dependencyKey(dependency: DependencyRef): string {
  return `${dependency.ecosystem}:${dependency.name}`
}

export interface SkippedDependency {
  name: string
  requested: string
  reason: string
}

export interface RegistryInfo {
  latestVersion: string
  registryUrl: string
  description: string | null
  license: string | null
  homepage: string | null
  repositoryUrl: string | null
  createdAt: string | null
  lastReleaseAt: string | null
  totalVersions: number
  releasesLastYear: number
  deprecated: string | null
  // Registry-specific extras; null where the registry doesn't expose them.
  maintainersCount: number | null
  dependenciesCount: number | null
  unpackedSizeBytes: number | null
  hasTypes: boolean | null
}

/** How widely a package is used; registries expose different measures. */
export interface Adoption {
  weeklyDownloads: number | null
  totalDownloads: number | null
  dependents: number | null
  note: string | null
}

export interface RepositoryInfo {
  fullName: string
  url: string
  description: string | null
  stars: number
  forks: number
  openIssues: number
  archived: boolean
  lastCommitAt: string | null
}

export interface Vulnerability {
  id: string
  summary: string | null
  severity: Severity
  aliases: string[]
  url: string
  affectsLatest: boolean
  affectsRequested: boolean | null
}

export interface VulnerabilityReport {
  totalKnown: number
  vulnerabilities: Vulnerability[]
  requestedVersion: string | null
  requestedPinned: boolean
}

export interface SourceIssue {
  source: DataSource
  message: string
}

export interface PackageSignals {
  dependency: DependencyRef
  registry: RegistryInfo | null
  adoption: Adoption | null
  repository: RepositoryInfo | null
  vulnerabilities: VulnerabilityReport | null
  issues: SourceIssue[]
}

export interface Finding {
  impact: "positive" | "negative" | "critical"
  message: string
  penalty: number
}

export interface Alternative {
  name: string
  reason: string
  url: string | null
  adoption: Adoption | null
}

export interface PackageAssessment {
  dependency: DependencyRef
  verdict: Verdict
  score: number | null
  summary: string
  reasons: string[]
  findings: Finding[]
  alternatives: Alternative[]
  signals: PackageSignals
  verdictSource: VerdictSource
  /** Jev's confidence in the verdict (0–1); null when the rules decided. */
  verdictConfidence: number | null
  explanationSource: "llm" | "heuristic"
}

export interface AnalysisReport {
  ecosystem: Ecosystem
  /** The detected dependency file format, e.g. "pyproject.toml"; null for a single package. */
  manifest: string | null
  overallVerdict: Verdict
  summary: string
  counts: Record<Verdict, number>
  assessments: PackageAssessment[]
  skipped: SkippedDependency[]
  generatedAt: string
}

/** Why an analysis couldn't finish, from the user's point of view. */
export type FailureKind = "unreachable" | "invalid" | "server"

export interface AnalysisFailure {
  kind: FailureKind
  message: string
  /** The backend's request ID (on every log line and trace of the request); quote it when reporting. */
  requestId?: string | null
}

export type AnalysisRequest =
  | { mode: "package"; ecosystem: EcosystemChoice; package: string }
  | { mode: "manifest"; content: string; filename?: string; includeDev: boolean }

/** How an "auto" package request was resolved to a registry. */
export interface EcosystemDetection {
  ecosystem: Ecosystem
  /** Other registries publishing a package with the same name, most used first. */
  alsoFoundIn: Ecosystem[]
}

export type AnalysisEvent =
  | {
      type: "plan"
      ecosystem: Ecosystem
      manifest: string | null
      detection: EcosystemDetection | null
      dependencies: DependencyRef[]
      skipped: SkippedDependency[]
    }
  | { type: "progress"; dependencyKey: string; step: AssessmentStep }
  | { type: "assessment"; assessment: PackageAssessment }
  | { type: "report"; report: AnalysisReport }
  | { type: "error"; kind: "invalid_input" | "internal"; message: string; requestId: string | null }
