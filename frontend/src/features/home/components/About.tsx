import ravi1 from '../../../assets/Ravi-1.png'
import { SectionHeading } from '../../../shared/ui/elements/SectionHeading'
import { profile } from '../content'

export function About() {
  return (
    <section className="section" id="about">
      <div className="container about-grid">
        <div className="about-photo">
          <img src={ravi1} alt={`${profile.name} at his desk`} loading="lazy" />
        </div>
        <div>
          <SectionHeading eyebrow="About me" title={`I build AI that does real work`} />
          <p>
            I'm {profile.name}, a {profile.profession.toLowerCase()} who spends his days turning
            language models into dependable software: agents that use tools, search engines over
            private documents, and the APIs and interfaces around them.
          </p>
          <p className="muted">
            I teach what I use. Every lesson here comes from something I've built, including the
            RAG chat you can try after logging in.
          </p>
          <h3 className="about-sub">Where I work</h3>
          <ul className="skill-list">
            {profile.expertise.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
