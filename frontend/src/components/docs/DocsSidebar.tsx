import { NavLink } from "react-router"

import { DOC_SECTIONS } from "@/docs/nav"
import { cn } from "@/lib/utils"

export function DocsSidebar({ onNavigate, className }: { onNavigate?: () => void; className?: string }) {
  return (
    <nav aria-label="Docs" className={cn("space-y-7 text-sm", className)}>
      {DOC_SECTIONS.map((section) => (
        <div key={section.title}>
          <p className="mb-2 px-3 text-xs font-semibold text-foreground">{section.title}</p>
          <ul className="space-y-0.5">
            {section.pages.map((page) => (
              <li key={page.slug}>
                <NavLink
                  to={`/docs/${page.slug}`}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      "block rounded-lg border border-transparent px-3 py-1.5 transition-colors",
                      isActive
                        ? "bg-background font-medium text-foreground shadow-sm dark:border-input dark:bg-input/30"
                        : "text-muted-foreground hover:text-foreground",
                    )
                  }
                >
                  {page.title}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
}
