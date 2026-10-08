import { useRef } from "react"

import { DemoSection } from "@/components/landing/DemoSection"
import { LandingHero } from "@/components/landing/LandingHero"

export default function LandingPage() {
  const demoRef = useRef<HTMLElement>(null)
  return (
    <main>
      <title>Package Health · Should I use this library?</title>
      <LandingHero onShowExample={() => demoRef.current?.scrollIntoView({ behavior: "smooth" })} />
      <DemoSection ref={demoRef} />
    </main>
  )
}
