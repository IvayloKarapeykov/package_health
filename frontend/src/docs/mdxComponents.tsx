import type { MDXComponents } from "mdx/types"

import { Note, Tip, Warning } from "@/components/docs/Callout"
import { Anchor, Heading, Pre } from "@/components/docs/MdxElements"
import { Steps } from "@/components/docs/Steps"

export const mdxComponents: MDXComponents = {
  h2: (props) => <Heading as="h2" {...props} className="mt-12 text-xl font-semibold tracking-tight" />,
  h3: (props) => <Heading as="h3" {...props} className="mt-8 text-base font-semibold" />,
  p: (props) => <p className="mt-4 leading-7 text-foreground/85" {...props} />,
  a: Anchor,
  ul: (props) => <ul className="mt-4 list-disc space-y-2 pl-5 leading-7 text-foreground/85 marker:text-brand-blue/50" {...props} />,
  ol: (props) => <ol className="mt-4 list-decimal space-y-2 pl-5 leading-7 text-foreground/85 marker:text-muted-foreground" {...props} />,
  strong: (props) => <strong className="font-semibold text-foreground" {...props} />,
  code: (props) => <code className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-foreground" {...props} />,
  pre: Pre,
  table: (props) => (
    <div className="glass-inset mt-6 overflow-x-auto rounded-xl">
      <table className="w-full text-left text-sm" {...props} />
    </div>
  ),
  th: (props) => <th className="border-b border-border px-4 py-2.5 font-medium whitespace-nowrap" {...props} />,
  td: (props) => <td className="border-b border-border/60 px-4 py-2.5 align-top text-foreground/85 [tr:last-child>&]:border-0" {...props} />,
  Note,
  Tip,
  Warning,
  Steps,
}
