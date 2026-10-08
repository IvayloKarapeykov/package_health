import { Link as LinkIcon } from "lucide-react"
import { type ComponentProps, isValidElement, type ReactElement, type ReactNode } from "react"
import { Link } from "react-router"

import { CodeBlock } from "@/components/editor/CodeBlock"
import type { CodeLanguage } from "@/components/editor/languages"

const LANGUAGES: Record<string, CodeLanguage> = {
  bash: "shell",
  sh: "shell",
  shell: "shell",
  json: "json",
  js: "javascript",
  javascript: "javascript",
  ts: "javascript",
  typescript: "javascript",
  python: "python",
  py: "python",
  toml: "toml",
  yaml: "yaml",
  xml: "xml",
  requirements: "requirements",
  gomod: "gomod",
}

type CodeProps = { className?: string; children?: ReactNode; "data-meta"?: string }

export function Pre({ children }: ComponentProps<"pre">) {
  if (!isValidElement(children)) return <pre>{children}</pre>
  const { className = "", children: text, "data-meta": meta } = (children as ReactElement<CodeProps>).props
  const name = className.replace("language-", "")
  const language = LANGUAGES[name]
  const title = meta?.match(/title="([^"]+)"/)?.[1] ?? (language === "shell" ? "terminal" : name || "text")
  return <CodeBlock title={title} code={String(text).replace(/\n$/, "")} language={language} className="mt-6" />
}

export function Heading({ as: Tag, id, children, className }: { as: "h2" | "h3"; id?: string; children?: ReactNode; className: string }) {
  return (
    <Tag id={id} className={`group scroll-mt-24 ${className}`}>
      {children}
      {id && (
        <a href={`#${id}`} aria-label="Link to this section" className="ml-2 inline-flex align-middle opacity-0 transition-opacity group-hover:opacity-100">
          <LinkIcon className="size-3.5 text-muted-foreground" />
        </a>
      )}
    </Tag>
  )
}

export function Anchor({ href = "", children }: ComponentProps<"a">) {
  const className = "font-medium text-brand-blue underline-offset-4 hover:underline"
  if (href.startsWith("/")) {
    return (
      <Link to={href} className={className}>
        {children}
      </Link>
    )
  }
  return (
    <a href={href} target={href.startsWith("#") ? undefined : "_blank"} rel="noreferrer" className={className}>
      {children}
    </a>
  )
}
