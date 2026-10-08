import { BadgeCheck, Sparkles } from "lucide-react"
import type { ReactNode } from "react"

import { VerdictBadge } from "@/components/analysis/VerdictBadge"
import { SectionHeading } from "@/components/landing/SectionHeading"
import { useDemo } from "@/demo"
import { describeAdoption, formatCompact } from "@/lib/format"
import { IMPACT_ICON } from "@/lib/verdict"
import type { PackageAssessment } from "@/types/analysis"

interface Step {
  title: string
  description: string
  output: ReactNode
}

function stepsFor(assessment: PackageAssessment): Step[] {
  const { signals, findings, alternatives } = assessment
  const adoption = describeAdoption(signals.adoption)
  const confidence = assessment.verdictConfidence
  return [
    {
      title: "Collect",
      description: "The registry, GitHub and OSV.dev, all queried in parallel.",
      output: (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
          <Fact value={adoption.value} label={adoption.label.toLowerCase()} />
          <Fact value={String(signals.registry?.releasesLastYear ?? "—")} label="releases in a year" />
          <Fact value={formatCompact(signals.repository?.stars)} label="GitHub stars" />
          <Fact value={String(signals.vulnerabilities?.totalKnown ?? "—")} label="advisories on record" />
        </dl>
      ),
    },
    {
      title: "Score",
      description: "Fixed rules, no AI. Every finding adds or takes away points.",
      output: (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <p className="font-mono text-3xl font-semibold tabular-nums">
            {assessment.score}
            <span className="text-base text-muted-foreground">/100</span>
          </p>
          <ul className="space-y-1.5 text-sm">
            {findings.map((finding) => {
              const { icon: Icon, className } = IMPACT_ICON[finding.impact]
              return (
                <li key={finding.message} className="flex gap-2">
                  <Icon className={`mt-0.5 size-4 shrink-0 ${className}`} aria-hidden />
                  {finding.message}
                </li>
              )
            })}
          </ul>
        </div>
      ),
    },
    {
      title: "Decide",
      description: "Jev, a decision model, picks the verdict. Critical problems go straight to avoid.",
      output: (
        <div className="flex flex-wrap items-center gap-3">
          <VerdictBadge verdict={assessment.verdict} size="lg" />
          {confidence != null && (
            <span className="font-mono text-sm text-muted-foreground">{Math.round(confidence * 100)}% confident</span>
          )}
        </div>
      ),
    },
    {
      title: "Explain",
      description: "An LLM writes the reasons, using only the facts collected above.",
      output: (
        <p className="flex gap-2.5 text-sm">
          <Sparkles className="mt-0.5 size-4 shrink-0 text-brand-blue" aria-hidden />
          {assessment.reasons[0] ?? assessment.summary}
        </p>
      ),
    },
    {
      title: "Verify",
      description: "Suggested alternatives are looked up in the registry, so none are made up.",
      output: (
        <ul className="space-y-2 text-sm">
          {alternatives.map((alternative) => (
            <li key={alternative.name} className="flex flex-wrap items-center gap-x-2.5 gap-y-0.5">
              <BadgeCheck className="size-4 shrink-0 text-success" aria-hidden />
              <span className="font-mono">{alternative.name}</span>
              <span className="text-xs text-muted-foreground">
                {describeAdoption(alternative.adoption).value} {describeAdoption(alternative.adoption).label.toLowerCase()}
              </span>
            </li>
          ))}
        </ul>
      ),
    },
  ]
}

export function HowItWorks() {
  const demo = useDemo("log4j")
  const assessment = demo?.report.assessments[0]

  return (
    <section className="mx-auto max-w-6xl px-4 py-24">
      <SectionHeading
        eyebrow="How it works"
        title="One package, five steps"
        description={
          <>
            Here is how <code className="font-mono text-foreground">log4j-core 2.14.1</code>, the version behind
            Log4Shell, gets its verdict.
          </>
        }
      />
      <ol className="mx-auto mt-14 max-w-3xl space-y-4">
        {assessment &&
          stepsFor(assessment).map((step, index) => (
            <li
              key={step.title}
              className="glass relative grid gap-4 rounded-2xl p-5 not-last:after:absolute not-last:after:top-full not-last:after:left-9 not-last:after:h-4 not-last:after:w-px not-last:after:bg-gradient-to-b not-last:after:from-brand-blue not-last:after:to-brand-cyan sm:grid-cols-[11rem_minmax(0,1fr)] sm:p-6"
            >
              <div>
                <span className="font-mono text-xs text-brand-blue">0{index + 1}</span>
                <h3 className="mt-1 font-semibold">{step.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{step.description}</p>
              </div>
              <div className="glass-inset self-center rounded-xl p-4">{step.output}</div>
            </li>
          ))}
      </ol>
    </section>
  )
}

function Fact({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <dt className="sr-only">{label}</dt>
      <dd className="font-mono text-xl font-semibold tabular-nums">{value}</dd>
      <dd className="text-xs text-muted-foreground">{label}</dd>
    </div>
  )
}
