import { ArrowRight, ArrowUpRight } from "lucide-react"
import { Link } from "react-router"

import { SectionHeading } from "@/components/landing/SectionHeading"

const TIERS = [
  {
    name: "No keys",
    description: "Rule-based verdicts and explanations. GitHub data shares a limit of 60 requests an hour.",
  },
  {
    name: "GitHub token",
    description: "Your own 5,000 GitHub requests an hour. A read-only token for public repositories is enough.",
    link: { label: "Create a token", href: "https://github.com/settings/personal-access-tokens" },
  },
  {
    name: "OpenRouter key",
    description: "Verdicts from Jev and explanations written by an LLM, billed to your own OpenRouter credits.",
    link: { label: "Get a key", href: "https://openrouter.ai/keys" },
  },
]

export function KeysSection() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-24">
      <SectionHeading
        eyebrow="Your keys"
        title="Free, because you bring the keys"
        description="No accounts and no paid plans. Your keys are used for your request only, and never stored or logged."
      />
      <ol className="glass mx-auto mt-12 max-w-3xl divide-y divide-border rounded-2xl">
        {TIERS.map((tier) => (
          <li key={tier.name} className="grid gap-1 px-6 py-5 sm:grid-cols-[10rem_minmax(0,1fr)] sm:gap-6">
            <p className="font-mono text-sm font-medium">{tier.name}</p>
            <div className="text-sm text-muted-foreground">
              {tier.description}
              {tier.link && (
                <a
                  href={tier.link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-1.5 inline-flex items-center gap-0.5 font-medium whitespace-nowrap text-brand-blue hover:underline"
                >
                  {tier.link.label}
                  <ArrowUpRight className="size-3.5" aria-hidden />
                </a>
              )}
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-6 text-center text-sm">
        <Link to="/app?keys" className="inline-flex items-center gap-1 font-medium text-brand-blue hover:underline">
          Add your keys in the analyzer
          <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </p>
    </section>
  )
}
