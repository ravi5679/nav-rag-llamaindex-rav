import { SectionHeading } from '../../../shared/ui/elements/SectionHeading'
import { learnTopics } from '../content'

export function WhatYoullLearn() {
  return (
    <section className="section section-alt" id="learn">
      <div className="container">
        <SectionHeading
          center
          eyebrow="Curriculum"
          title="What you'll learn"
          subtitle="From first principles to a working AI product, in the order that makes sense."
        />
        <div className="card-grid">
          {learnTopics.map((t, i) => (
            <article className="card" key={t.title}>
              <span className="card-num">{String(i + 1).padStart(2, '0')}</span>
              <h3>{t.title}</h3>
              <p className="muted">{t.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
