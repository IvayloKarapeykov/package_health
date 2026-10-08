import { ArrowUpRight, Eye, EyeOff, KeyRound, ShieldCheck, X } from "lucide-react"
import { Dialog } from "radix-ui"
import { type FormEvent, useId, useState } from "react"

import { Input } from "@/components/ui/input"
import { useKeys } from "@/hooks/useKeys"
import { type ApiKeys, clearKeys, hasKeys, saveKeys } from "@/lib/keys"
import { GITHUB_URL } from "@/lib/links"
import { cn } from "@/lib/utils"

interface KeysDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  className?: string
}

export function KeysDialog({ open, onOpenChange, className }: KeysDialogProps) {
  const keys = useKeys()
  const active = hasKeys(keys)

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger
        className={cn(
          "glass-inset flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-sm font-medium text-foreground/60 transition-colors hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none dark:text-muted-foreground dark:hover:text-foreground",
          className,
        )}
      >
        <KeyRound className="size-4" aria-hidden />
        {active ? "Your keys" : "Add keys"}
        {active && <span className="size-1.5 rounded-full bg-success" aria-label="Keys saved" />}
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-[2px] dark:bg-black/50 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 border border-border bg-popover text-popover-foreground shadow-2xl shadow-slate-900/20 max-h-[calc(100svh-2rem)] w-[calc(100%-2rem)] max-w-lg -translate-1/2 overflow-y-auto rounded-2xl p-6 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95">
          {/* Remounts on each open, so the fields start from what's saved. */}
          {open && <KeysForm saved={keys} onDone={() => onOpenChange(false)} />}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function KeysForm({ saved, onDone }: { saved: ApiKeys; onDone: () => void }) {
  const [githubToken, setGithubToken] = useState(saved.githubToken)
  const [openRouterKey, setOpenRouterKey] = useState(saved.openRouterKey)
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const result = saveKeys({ githubToken, openRouterKey })
    if (result === "ok") onDone()
    else setError("This browser didn't allow saving them. Private windows sometimes block storage.")
  }

  function handleRemove() {
    clearKeys()
    onDone()
  }

  return (
    <form onSubmit={handleSubmit}>
      <Dialog.Title className="pr-8 text-lg font-semibold">Your keys</Dialog.Title>
      <Dialog.Description className="mt-1 pr-8 text-sm text-muted-foreground">
        Both are optional. Without them, verdicts come from fixed rules and GitHub data shares a limit of 60 requests
        an hour with everyone using the site.
      </Dialog.Description>

      <div className="mt-6 space-y-5">
        <KeyField
          label="GitHub token"
          value={githubToken}
          onChange={setGithubToken}
          placeholder="github_pat_…"
          link={{ label: "Create one", href: "https://github.com/settings/personal-access-tokens/new" }}
          warning={githubToken && !/^(github_pat_|ghp_|gho_)/.test(githubToken.trim()) ? "This doesn't look like a GitHub token." : null}
        >
          Gives you your own 5,000 GitHub requests an hour. Choose public repository access only: such a token can
          read public data and nothing else.
        </KeyField>
        <KeyField
          label="OpenRouter key"
          value={openRouterKey}
          onChange={setOpenRouterKey}
          placeholder="sk-or-…"
          link={{ label: "Get one", href: "https://openrouter.ai/keys" }}
          warning={openRouterKey && !openRouterKey.trim().startsWith("sk-or-") ? "This doesn't look like an OpenRouter key." : null}
        >
          Adds verdicts from Jev and written explanations, billed to your OpenRouter credits. You can give the key a
          spending limit.
        </KeyField>
      </div>

      <section className="mt-6 rounded-xl border border-border bg-muted/50 p-4 text-sm">
        <h3 className="flex items-center gap-2 font-medium">
          <ShieldCheck className="size-4 text-success" aria-hidden />
          How your keys are handled
        </h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground marker:text-border">
          <li>They're saved in this browser only. There's no account.</li>
          <li>Each check sends them over HTTPS to the analysis server, which uses them for that check and never saves or logs them.</li>
          <li>
            You can verify this:{" "}
            <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="text-brand-blue hover:underline">
              the code is open source
            </a>
            .
          </li>
        </ul>
      </section>

      {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

      <div className="mt-6 flex items-center justify-between gap-3">
        {hasKeys(saved) ? (
          <button
            type="button"
            onClick={handleRemove}
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-destructive"
          >
            Remove keys
          </button>
        ) : (
          <span />
        )}
        <button
          type="submit"
          className="h-10 rounded-full bg-gradient-to-r from-brand-blue to-brand-cyan px-5 text-sm font-medium text-white shadow-lg shadow-brand-blue/25 transition hover:brightness-110 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          Save
        </button>
      </div>

      {/* Last in tab order, so opening the dialog focuses the first field. */}
      <Dialog.Close
        aria-label="Close"
        className="absolute top-5 right-4 grid size-8 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
      >
        <X className="size-4" />
      </Dialog.Close>
    </form>
  )
}

interface KeyFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
  link: { label: string; href: string }
  warning: string | null
  children: string
}

function KeyField({ label, value, onChange, placeholder, link, warning, children }: KeyFieldProps) {
  const id = useId()
  const [visible, setVisible] = useState(false)
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <label htmlFor={id} className="text-sm font-medium">
          {label}
        </label>
        <a
          href={link.href}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-0.5 text-xs font-medium text-brand-blue hover:underline"
        >
          {link.label}
          <ArrowUpRight className="size-3" aria-hidden />
        </a>
      </div>
      <div className="relative mt-1.5">
        <Input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
          data-1p-ignore
          className="h-10 rounded-lg pr-10 font-mono text-sm md:text-sm"
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? `Hide ${label}` : `Show ${label}`}
          className="absolute top-1/2 right-1.5 grid size-7 -translate-y-1/2 place-items-center rounded-md text-muted-foreground hover:text-foreground"
        >
          {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>
      </div>
      <p className={cn("mt-1.5 text-xs", warning ? "text-warning-foreground" : "text-muted-foreground")}>
        {warning ?? children}
      </p>
    </div>
  )
}
