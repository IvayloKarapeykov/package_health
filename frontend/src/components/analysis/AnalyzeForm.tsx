import { FileCode2, PackageSearch, Search } from "lucide-react"
import { lazy, Suspense, useState, type FormEvent } from "react"

import { EcosystemSelect } from "@/components/analysis/EcosystemSelect"
import { ManifestExamplesMenu } from "@/components/analysis/ManifestExamplesMenu"
import { WaveLine } from "@/components/effects/WaveLine"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ECOSYSTEM_CHOICE_BY_ID, MANIFEST_EXAMPLES } from "@/lib/ecosystems"
import type { AnalysisRequest, EcosystemChoice } from "@/types/analysis"

// The editor (CodeMirror) loads only when the dependency file tab is first opened.
const ManifestEditor = lazy(() => import("@/components/editor/ManifestEditor"))

type Mode = AnalysisRequest["mode"]

// The editor doesn't wrap lines, so the supported formats are listed a few per line.
const FORMATS_PER_LINE = 4
const EDITOR_PLACEHOLDER = [
  "Paste a dependency file — the format is detected automatically.",
  "",
  ...chunk(MANIFEST_EXAMPLES.map((example) => example.format), FORMATS_PER_LINE).map((row) => row.join("  ·  ")),
].join("\n")

function chunk<T>(items: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(items.length / size) }, (_, i) => items.slice(i * size, (i + 1) * size))
}

interface AnalyzeFormProps {
  running: boolean
  onSubmit: (request: AnalysisRequest) => void
}

export function AnalyzeForm({ running, onSubmit }: AnalyzeFormProps) {
  const [mode, setMode] = useState<Mode>("package")
  const [ecosystem, setEcosystem] = useState<EcosystemChoice>("auto")
  const [packageName, setPackageName] = useState("")
  const [manifest, setManifest] = useState("")
  const [includeDev, setIncludeDev] = useState(true)

  const meta = ECOSYSTEM_CHOICE_BY_ID[ecosystem]
  const canSubmit = !running && (mode === "package" ? packageName.trim() : manifest.trim())

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canSubmit) return
    onSubmit(
      mode === "package"
        ? { mode, ecosystem, package: packageName.trim() }
        : { mode, content: manifest, includeDev },
    )
  }

  function analyzeExample(name: string) {
    setPackageName(name)
    onSubmit({ mode: "package", ecosystem, package: name })
  }

  return (
    <form onSubmit={handleSubmit}>
      <Tabs value={mode} onValueChange={(value) => setMode(value as Mode)}>
        <TabsList className="glass-inset">
          <TabsTrigger value="package">
            <PackageSearch /> Package
          </TabsTrigger>
          <TabsTrigger value="manifest">
            <FileCode2 /> Dependency file
          </TabsTrigger>
        </TabsList>

        <TabsContent value="package" className="mt-4 space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <EcosystemSelect value={ecosystem} onChange={setEcosystem} disabled={running} className="w-full sm:w-44" />
            <div className="flex flex-1 gap-2">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={packageName}
                  onChange={(event) => setPackageName(event.target.value)}
                  placeholder={meta.placeholder}
                  aria-label="Package name"
                  className="glass-inset h-12 rounded-xl pl-10 font-mono text-base md:text-base"
                  autoFocus
                  spellCheck={false}
                  autoCapitalize="off"
                />
              </div>
              <SubmitButton running={running} disabled={!canSubmit} />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 pl-1 text-xs text-muted-foreground">
            Try:
            {meta.examples.map((name) => (
              <Button
                key={name}
                type="button"
                variant="ghost"
                size="xs"
                className="glass-inset rounded-full px-2.5 font-mono hover:border-brand-cyan/60"
                disabled={running}
                onClick={() => analyzeExample(name)}
              >
                {name}
              </Button>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="manifest" className="mt-4 space-y-3">
          <Suspense fallback={<div className="glass-inset h-[calc(14rem+2.25rem)] animate-pulse rounded-xl" />}>
            <ManifestEditor
              value={manifest}
              onChange={setManifest}
              placeholder={EDITOR_PLACEHOLDER}
              ariaLabel="Dependency file contents"
            />
          </Suspense>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch id="include-dev" checked={includeDev} onCheckedChange={setIncludeDev} />
                <Label htmlFor="include-dev">Include dev dependencies</Label>
              </div>
              <ManifestExamplesMenu onPick={setManifest} />
            </div>
            <SubmitButton running={running} disabled={!canSubmit} />
          </div>
        </TabsContent>
      </Tabs>
    </form>
  )
}

function SubmitButton({ running, disabled }: { running: boolean; disabled: boolean }) {
  return (
    <Button
      type="submit"
      size="lg"
      className="h-12 rounded-xl bg-gradient-to-r from-brand-blue to-brand-cyan px-5 text-white shadow-lg shadow-brand-blue/25 transition hover:brightness-110 disabled:opacity-60"
      disabled={disabled}
    >
      {running ? <WaveLine className="h-3.5 w-7" wavelength={200} amplitude={8} strokeWidth={2} duration="0.9s" /> : <Search />}
      {running ? "Analyzing…" : "Analyze"}
    </Button>
  )
}
