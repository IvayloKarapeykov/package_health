import type { ReactNode } from "react"

/** Numbers each `###` heading inside it and joins them with a line, for step-by-step guides. */
export function Steps({ children }: { children: ReactNode }) {
  return (
    <div className="mt-8 ml-3.5 border-l border-border pl-8 [counter-reset:step] [&>h3]:relative [&>h3]:mt-10 [&>h3:first-child]:mt-0 [&>h3]:[counter-increment:step] [&>h3]:before:absolute [&>h3]:before:top-1/2 [&>h3]:before:-left-[2.85rem] [&>h3]:before:grid [&>h3]:before:size-7 [&>h3]:before:-translate-y-1/2 [&>h3]:before:place-items-center [&>h3]:before:rounded-full [&>h3]:before:bg-background [&>h3]:before:font-mono [&>h3]:before:text-xs [&>h3]:before:text-brand-blue [&>h3]:before:ring-1 [&>h3]:before:ring-border [&>h3]:before:content-[counter(step)]">
      {children}
    </div>
  )
}
