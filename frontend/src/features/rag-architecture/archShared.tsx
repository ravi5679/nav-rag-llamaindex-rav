import sessionGif from '../../assets/session-flow.gif'
import type { RagType } from '../../shared/endpoints'
import { dataLocations, sessionSteps, type Step } from './archSteps'
import './rag-architecture.css'

type Tone = 'ingest' | 'query' | 'session' | 'hybrid'

export function StepList({ title, endpoint, steps, tone }: { title: string; endpoint: string; steps: Step[]; tone: Tone }) {
  return (
    <section className={`arch-card arch-steps ${tone}`}>
      <header>
        <h3>{title}</h3>
        <code>{endpoint}</code>
      </header>
      <ol>
        {steps.map((s) => (
          <li key={s.name}>
            <strong>{s.name}</strong>
            <span className="muted">{s.what}</span>
            <code>{s.code}</code>
          </li>
        ))}
      </ol>
    </section>
  )
}

/** Login + session lifecycle: the same for every RAG type. */
export function SessionSection({ rag }: { rag: RagType }) {
  return (
    <>
      <h2 className="arch-heading">Login &amp; session lifecycle</h2>
      <section className="arch-card arch-flow">
        <img
          src={sessionGif}
          alt="Animated session lifecycle: Login or sign up, the server returns a token and session id, the user uploads and asks, the session ends by logout or after 60 minutes idle or 24 hours, then the file, vectors and index are deleted."
          width={1200}
          height={380}
        />
      </section>

      <div className="arch-grid">
        <StepList title="Session" endpoint="POST /api/v1/auth/login" steps={sessionSteps} tone="session" />

        <section className="arch-card arch-steps data">
          <header>
            <h3>Where data lives</h3>
            <code>backend/</code>
          </header>
          <div className="arch-table" role="table" aria-label="Where data lives">
            {dataLocations(rag).map((d) => (
              <div className="arch-row" role="row" key={d.path}>
                <code role="cell">{d.path}</code>
                <span role="cell" className="muted">{d.what}</span>
                <span role="cell" className={`arch-life ${d.lifetime === 'Permanent' ? 'keep' : 'temp'}`}>{d.lifetime}</span>
              </div>
            ))}
          </div>
          <p className="muted arch-small">
            "Session" items are deleted on logout, after 60 minutes without activity, or 24 hours after login.
          </p>
        </section>
      </div>
    </>
  )
}
