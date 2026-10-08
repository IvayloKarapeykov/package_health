import { useState } from "react"

import { CodeBlock } from "@/components/editor/CodeBlock"
import type { CodeLanguage } from "@/components/editor/languages"
import { SectionHeading } from "@/components/landing/SectionHeading"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MCP_URL } from "@/lib/links"

const TOKEN_HEADER = `"X-GitHub-Token": "github_pat_..."`

const CLIENTS: { id: string; label: string; file: string; language: CodeLanguage; code: string }[] = [
  {
    id: "claude",
    label: "Claude Code",
    file: "terminal",
    language: "shell",
    code: `claude mcp add --transport http package-health \\
  ${MCP_URL} \\
  --header "X-GitHub-Token: github_pat_..."`,
  },
  {
    id: "cursor",
    label: "Cursor",
    file: "~/.cursor/mcp.json",
    language: "json",
    code: `{
  "mcpServers": {
    "package-health": {
      "url": "${MCP_URL}",
      "headers": { ${TOKEN_HEADER} }
    }
  }
}`,
  },
  {
    id: "vscode",
    label: "VS Code",
    file: ".vscode/mcp.json",
    language: "json",
    code: `{
  "servers": {
    "package-health": {
      "type": "http",
      "url": "${MCP_URL}",
      "headers": { ${TOKEN_HEADER} }
    }
  }
}`,
  },
]

const TOOLS = [
  { name: "check_package", description: "One package, like express or requests>=2.31" },
  { name: "check_dependencies", description: "Every dependency in a file's contents" },
]

export function AgentsSection() {
  const [clientId, setClientId] = useState(CLIENTS[0].id)
  const client = CLIENTS.find((entry) => entry.id === clientId)!

  return (
    <section className="mx-auto max-w-6xl px-4 py-24">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <div>
          <SectionHeading
            eyebrow="For AI agents"
            title="Let your agent check before it installs"
            description="Coding agents add dependencies all the time. Connect them over MCP and they can check a package before it lands in your project."
            className="text-left lg:mx-0"
          />
          <ul className="mt-8 space-y-3">
            {TOOLS.map((tool) => (
              <li key={tool.name} className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:gap-3">
                <code className="font-mono text-sm font-medium text-brand-blue">{tool.name}</code>
                <span className="text-sm text-muted-foreground">{tool.description}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="glass min-w-0 rounded-2xl p-4 sm:p-5">
          <Tabs value={clientId} onValueChange={setClientId}>
            <TabsList className="glass-inset">
              {CLIENTS.map((entry) => (
                <TabsTrigger key={entry.id} value={entry.id}>
                  {entry.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <CodeBlock title={client.file} code={client.code} language={client.language} className="mt-4" />
          <p className="mt-3 px-1 text-xs text-muted-foreground">
            The token is optional but gives you your own GitHub rate limit. Add an{" "}
            <code className="font-mono whitespace-nowrap">X-OpenRouter-Key</code> header for AI-written explanations.
          </p>
        </div>
      </div>
    </section>
  )
}
