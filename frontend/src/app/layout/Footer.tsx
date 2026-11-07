import { Link } from 'react-router-dom'
import { profile } from '../../features/home/content'
import { GithubIcon, LinkedinIcon, MailIcon } from '../../shared/ui/elements/Icons'
import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="footer" id="contact">
      <div className="container footer-grid">
        <div>
          <Logo />
          <p className="muted footer-tag">{profile.tagline}</p>
        </div>

        <div>
          <h4>Explore</h4>
          <ul className="footer-links">
            <li><Link to="/#about">About</Link></li>
            <li><Link to="/#learn">What you'll learn</Link></li>
            <li><Link to="/#projects">Projects</Link></li>
            <li><Link to="/login">Login</Link></li>
          </ul>
        </div>

        <div>
          <h4>Get in touch</h4>
          <p className="muted">
            <a href={profile.links.email}>{profile.emailLabel}</a>
          </p>
          <div className="socials">
            <a href={profile.links.linkedin} target="_blank" rel="noreferrer" aria-label="LinkedIn">
              <LinkedinIcon />
            </a>
            <a href={profile.links.github} target="_blank" rel="noreferrer" aria-label="GitHub">
              <GithubIcon />
            </a>
            <a href={profile.links.email} aria-label="Email">
              <MailIcon />
            </a>
          </div>
        </div>
      </div>
      <div className="container footer-bottom">
        <span>© {new Date().getFullYear()} {profile.name}. All rights reserved.</span>
      </div>
    </footer>
  )
}
