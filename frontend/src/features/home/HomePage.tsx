import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { About } from './components/About'
import { CtaBand } from './components/CtaBand'
import { FeaturedProjects } from './components/FeaturedProjects'
import { Hero } from './components/Hero'
import { WhatYoullLearn } from './components/WhatYoullLearn'
import './home.css'

export function HomePage() {
  const { hash } = useLocation()

  // Router doesn't scroll to #anchors by itself (e.g. coming from /login via "/#about")
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView()
    else window.scrollTo(0, 0)
  }, [hash])

  return (
    <>
      <Hero />
      <About />
      <WhatYoullLearn />
      <FeaturedProjects />
      <CtaBand />
    </>
  )
}
