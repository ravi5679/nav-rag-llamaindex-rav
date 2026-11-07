import { Link } from 'react-router-dom'
import ravi3 from '../../../assets/Ravi-3.png'
import { useAuth } from '../../auth/useAuth'
import { ArrowRightIcon } from '../../../shared/ui/elements/Icons'
import { heroChips, profile } from '../content'

export function Hero() {
  const { user } = useAuth()
  return (
    <section className="hero" id="top">
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="eyebrow">Learn AI by building it</span>
          <h1>
            Hi, I'm <span className="gradient-text">{profile.name}</span>
          </h1>
          <p className="hero-tagline">{profile.tagline}</p>
          <p className="muted hero-sub">
            Practical, hands-on lessons on LLMs, RAG and AI agents from a working{' '}
            {profile.profession.toLowerCase()}. No hype, just things that run.
          </p>
          <div className="hero-actions">
            <Link to={user ? '/dashboard' : '/login'} className="btn btn-primary btn-lg">
              Get Started <ArrowRightIcon width={18} height={18} />
            </Link>
            <Link to="/#learn" className="btn btn-ghost btn-lg">
              What you'll learn
            </Link>
          </div>
          <ul className="chips">
            {heroChips.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>

        <div className="hero-photo">
          <div className="hero-glow" />
          <img src={ravi3} alt={`${profile.name}, ${profile.profession}`} />
        </div>
      </div>
    </section>
  )
}
