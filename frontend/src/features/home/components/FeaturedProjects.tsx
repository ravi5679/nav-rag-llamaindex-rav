import { GithubIcon } from '../../../shared/ui/elements/Icons'
import { SectionHeading } from '../../../shared/ui/elements/SectionHeading'
import { projects } from '../content'

export function FeaturedProjects() {
  return (
    <section className="section" id="projects">
      <div className="container">
        <SectionHeading
          center
          eyebrow="Featured"
          title="Projects you can learn from"
          subtitle="Real builds, with the code to read, run and adapt."
        />
        <div className="card-grid three">
          {projects.map((p) => (
            <article className="card project" key={p.title}>
              <h3>{p.title}</h3>
              <p className="muted">{p.text}</p>
              <ul className="chips small">
                {p.tags.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
              <a className="card-link" href={p.href} target="_blank" rel="noreferrer">
                <GithubIcon width={16} height={16} /> View on GitHub
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
