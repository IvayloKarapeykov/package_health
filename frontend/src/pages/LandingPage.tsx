import { useRef } from "react"

import { AgentsSection } from "@/components/landing/AgentsSection"
import { DemoSection } from "@/components/landing/DemoSection"
import { HowItWorks } from "@/components/landing/HowItWorks"
import { KeysSection } from "@/components/landing/KeysSection"
import { SiteFooter } from "@/components/layout/SiteFooter"
import { LandingHero } from "@/components/landing/LandingHero"

export default function LandingPage() {
  const demoRef = useRef<HTMLElement>(null)
  return (
    <>
      <main>
        <title>Package Health · Should I use this library?</title>
        <LandingHero onShowExample={() => demoRef.current?.scrollIntoView({ behavior: "smooth" })} />
        <DemoSection ref={demoRef} />
        <HowItWorks />
        <AgentsSection />
        <KeysSection />
      </main>
      <SiteFooter />
    </>
  )
}
