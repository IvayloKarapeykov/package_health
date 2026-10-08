/** Follows the backend parsers' detection order (app/manifests), so the two normally agree. */

import type { Ecosystem } from "@/types/analysis"

export type Syntax = "json" | "xml" | "yaml" | "toml" | "ruby" | "groovy" | "kotlin" | "gomod" | "requirements"

export interface ManifestFormat {
  /** e.g. "pom.xml"; shown as the editor's file tab. */
  name: string
  ecosystem: Ecosystem
  syntax: Syntax
}

// Enough to recognize any format; keeps detection cheap on every keystroke in large files.
const SAMPLE_CHARS = 16_000

const RULES: { format: ManifestFormat; matches: (text: string) => boolean }[] = [
  rule("package-lock.json", "npm", "json", (t) => t.startsWith("{") && /"lockfileVersion"\s*:/.test(t)),
  rule("pnpm-lock.yaml", "npm", "yaml", (t) => /^lockfileVersion:/m.test(t)),
  rule("composer.json", "packagist", "json", (t) => t.startsWith("{") && /"require(-dev)?"\s*:/.test(t)),
  rule("package.json", "npm", "json", (t) => t.startsWith("{")),
  rule(".csproj", "nuget", "xml", (t) => t.startsWith("<") && /<Project\b[^>]*Sdk=|<PackageReference\b/.test(t)),
  rule("pom.xml", "maven", "xml", (t) => t.startsWith("<") && /<project\b|<dependencies>/.test(t)),
  rule("Cargo.toml", "cargo", "toml", (t) => /^\[package\]/m.test(t) || /^\[(workspace\.)?dependencies\]/m.test(t)),
  rule("pyproject.toml", "pypi", "toml", (t) => /^\[(project|tool\.poetry)[\].]/m.test(t)),
  rule("Pipfile", "pypi", "toml", (t) => /^\[\[source\]\]|^\[(dev-)?packages\]/m.test(t)),
  rule("go.mod", "go", "gomod", (t) => /^module\s+\S+/m.test(t)),
  rule("build.gradle.kts", "maven", "kotlin", (t) => /^\s*(implementation|api|testImplementation)\s*\(\s*"/m.test(t)),
  rule("build.gradle", "maven", "groovy", (t) => /^\s*(implementation|api|testImplementation|compileOnly)\s+['"]/m.test(t)),
  rule("Gemfile", "rubygems", "ruby", (t) => /^\s*(source\s+['"]https?:|gem\s+['"])/m.test(t)),
  rule("requirements.txt", "pypi", "requirements", looksLikeRequirements),
]

export function detectManifestFormat(content: string): ManifestFormat | null {
  const text = content.slice(0, SAMPLE_CHARS).trimStart()
  if (!text) return null
  return RULES.find((candidate) => candidate.matches(text))?.format ?? null
}

function rule(name: string, ecosystem: Ecosystem, syntax: Syntax, matches: (text: string) => boolean) {
  return { format: { name, ecosystem, syntax }, matches }
}

/** Mostly lines like `name`, `name==1.2`, `name[extra]>=1; marker` (comments and options aside). */
function looksLikeRequirements(text: string): boolean {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#") && !line.startsWith("-"))
  if (!lines.length) return false
  const specs = lines.filter((line) => /^[A-Za-z0-9][\w.-]*\s*(\[[^\]]*\])?\s*([=<>!~]=?.*|;.*|@.*)?$/.test(line))
  return specs.length / lines.length >= 0.8
}
