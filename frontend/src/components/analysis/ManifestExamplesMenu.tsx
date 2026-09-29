import { ChevronDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ECOSYSTEM_BY_ID, MANIFEST_EXAMPLES } from "@/lib/ecosystems"

interface ManifestExamplesMenuProps {
  onPick: (content: string) => void
}

/** "Load example" menu with one realistic dependency file per supported format. */
export function ManifestExamplesMenu({ onPick }: ManifestExamplesMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="link" size="sm" className="px-0">
          Load example <ChevronDown className="size-3.5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel className="text-xs text-muted-foreground">Example dependency files</DropdownMenuLabel>
        {MANIFEST_EXAMPLES.map((example) => (
          <DropdownMenuItem key={example.format} onSelect={() => onPick(example.content)}>
            <span className="font-mono text-xs">{example.format}</span>
            <span className="ml-auto text-xs text-muted-foreground">{ECOSYSTEM_BY_ID[example.ecosystem].label}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
