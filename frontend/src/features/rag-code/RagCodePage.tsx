import { CodeBlock } from './CodeBlock'
import { hybridLibraries, hybridSteps } from './hybridRagSteps'
import { naiveLibraries, naiveSteps, type CodeStep, type Library } from './naiveRagSteps'
import './rag-code.css'

export const NaiveRagCodePage = () => <RagCodePage libraries={naiveLibraries} steps={naiveSteps} />
export const HybridRagCodePage = () => <RagCodePage libraries={hybridLibraries} steps={hybridSteps} />

function RagCodePage({ libraries, steps }: { libraries: Library[]; steps: CodeStep[] }) {
  return (
    <div className="code-page">
      <nav className="code-toc" aria-label="Steps">
        <p className="code-toc-title">Steps</p>
        <ol>
          {steps.map((s) => (
            <li key={s.id}>
              <a href={`#step-${s.id}`}>{s.title}</a>
            </li>
          ))}
        </ol>
      </nav>

      <div className="code-main">
        <section className="code-card">
          <h2>Libraries used</h2>
          <p className="muted">
            The same packages the backend uses (versions from <code>backend/uv.lock</code>). The snippets
            below are simplified from <code>backend/rag_steps/</code>.
          </p>
          <div className="lib-table" role="table" aria-label="Libraries">
            {libraries.map((l) => (
              <div className="lib-row" role="row" key={l.name}>
                <code role="cell">{l.name}</code>
                <span role="cell" className="lib-version">{l.version}</span>
                <span role="cell" className="muted">{l.usedFor}</span>
              </div>
            ))}
          </div>
        </section>

        {steps.map((s) => (
          <section key={s.id} id={`step-${s.id}`} className="code-card code-step">
            <header>
              <h2>{s.title}</h2>
              <div className="code-tags">
                {s.libraries.map((lib) => (
                  <span key={lib} className="code-tag">{lib}</span>
                ))}
              </div>
            </header>
            <p className="muted">{s.summary}</p>
            <CodeBlock code={s.code} lang={s.lang} />
            <p className="code-file">
              In this project: <code>{s.file}</code>
            </p>
          </section>
        ))}
      </div>
    </div>
  )
}
