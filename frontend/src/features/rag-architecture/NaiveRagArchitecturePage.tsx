import flowGif from '../../assets/naive-rag-flow.gif'
import { SessionSection, StepList } from './archShared'
import { ingestSteps, type Step } from './archSteps'

// Keep in sync with backend/naive_rag/ and scripts/make_naive_rag_flow_gif.py
const querySteps: Step[] = [
  { name: 'Question', what: 'The chat sends { question, top_k } with the login token and X-Session-Id.', code: 'common/rag_routes.py' },
  { name: 'Embed query', what: 'Same embedding model, so question and chunks are comparable.', code: 'rag_steps/query_engine.py' },
  { name: 'Retrieve', what: 'VectorIndexRetriever: the top-k closest chunks from this session’s LanceDB.', code: 'rag_steps/query_engine.py' },
  { name: 'Build prompt', what: 'Response synthesizer combines the chunks and the question.', code: 'rag_steps/query_engine.py' },
  { name: 'Generate', what: 'gpt-4o-mini answers from that context; sources are returned too.', code: 'naive_rag/pipeline.py' },
]

export function NaiveRagArchitecturePage() {
  return (
    <div className="arch-page">
      <h2 className="arch-heading">RAG flow</h2>
      <section className="arch-card arch-flow">
        <img
          src={flowGif}
          alt="Animated Naive RAG flow. Ingestion: Upload, Chunk, Embed, Vector DB and index. Query: Question, Embed query, Retrieve by similarity search from LanceDB, Build prompt, Generate."
          width={1200}
          height={410}
        />
      </section>

      <div className="arch-grid">
        <StepList title="1 · Ingestion" endpoint="POST /api/v1/naive/ingest" steps={ingestSteps('naive')} tone="ingest" />
        <StepList title="2 · Query" endpoint="POST /api/v1/naive/query" steps={querySteps} tone="query" />
      </div>

      <p className="muted arch-note">
        Ingestion and query must use the <strong>same embedding model</strong>; otherwise the question vector
        can't be compared with the stored chunk vectors.
      </p>

      <SessionSection rag="naive" />
    </div>
  )
}
