import { Children, isValidElement, type ReactElement, type ReactNode, useState } from "react"

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"

type FenceProps = { children?: ReactElement<{ "data-meta"?: string; className?: string }> }

/** Shows several code fences as tabs, labelled by each fence's title="...". */
export function CodeTabs({ children }: { children: ReactNode }) {
  const blocks = Children.toArray(children).filter(isValidElement) as ReactElement<FenceProps>[]
  const labels = blocks.map((block, index) => {
    const code = block.props.children?.props
    return code?.["data-meta"]?.match(/title="([^"]+)"/)?.[1] ?? code?.className?.replace("language-", "") ?? `Example ${index + 1}`
  })
  const [active, setActive] = useState(0)

  return (
    <div className="mt-6 [&>div:last-child>*]:mt-3">
      <Tabs value={String(active)} onValueChange={(value) => setActive(Number(value))}>
        <TabsList className="glass-inset">
          {labels.map((label, index) => (
            <TabsTrigger key={label} value={String(index)} className="px-2.5 text-xs">
              {label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <div>{blocks[active]}</div>
    </div>
  )
}
