import flowGif from '../../assets/hybrid-rag-flow.gif'
import { SessionSection, StepList } from './archShared'
import { ingestSteps, type Step } from './archSteps'

// Keep in sync with backend/hybrid_rag/, rag_steps/hybrid_retriever.py and scripts/make_hybrid_rag_flow_gif.py
const querySteps: Step[] = [
  { name: 'Question', what: 'The chat sends { question, top_k } with the login token and X-Session-Id.', code: 'common/rag_routes.py' },
  { name: 'Vector search', what: 'Embed the question, fetch the 5 chunks closest in meaning (VectorIndexRetriever).', code: 'rag_steps/query_engine.py' },
  { name: 'Keyword search (BM25)', what: 'LanceDB full-text search on the same table: the 5 chunks with the best keyword match.', code: 'rag_steps/hybrid_retriever.py' },
  { name: 'Fuse (RRF)', what: 'QueryFusionRetriever merges both ranked lists with Reciprocal Rank Fusion and keeps the top 4.', code: 'rag_steps/hybrid_retriever.py' },
  { name: 'Build prompt + generate', what: 'Fused chunks + question go to gpt-4o-mini; answer and sources are returned.', code: 'hybrid_rag/pipeline.py' },
]

const comparison = [
  { label: 'Finds', naive: 'Chunks with similar meaning', hybrid: 'Similar meaning AND exact words' },
  { label: 'Good at', naive: 'Paraphrases, synonyms, vague questions', hybrid: 'Also codes, IDs, names, rare terms' },
  { label: 'Searches', naive: '1 (vector)', hybrid: '2 (vector + BM25), run in parallel' },
  { label: 'Ingestion', naive: 'Upload → Chunk → Embed → Vector DB', hybrid: 'Identical' },
]

export function HybridRagArchitecturePage() {
  return (
    <div className="arch-page">
      <h2 className="arch-heading">RAG flow</h2>
      <section className="arch-card arch-flow">
        <img
          src={flowGif}
          alt="Animated Hybrid RAG flow. Ingestion: Upload, Chunk, Embed, Vector DB and index. Query: the question goes to a vector search and a BM25 keyword search in parallel, both result lists are fused with reciprocal rank fusion, then the prompt is built and the LLM generates the answer."
          width={1200}
          height={480}
        />
      </section>

      <div className="arch-grid">
        <StepList title="1 · Ingestion" endpoint="POST /api/v1/hybrid/ingest" steps={ingestSteps('hybrid')} tone="ingest" />
        <StepList title="2 · Query" endpoint="POST /api/v1/hybrid/query" steps={querySteps} tone="hybrid" />
      </div>

      <section className="arch-card arch-steps">
        <header>
          <h3>Naive vs Hybrid</h3>
          <code>only retrieval differs</code>
        </header>
        <div className="arch-table" role="table" aria-label="Naive vs Hybrid RAG">
          <div className="arch-row arch-compare arch-compare-head" role="row">
            <span role="columnheader" />
            <span role="columnheader">Naive RAG</span>
            <span role="columnheader">Hybrid RAG</span>
          </div>
          {comparison.map((c) => (
            <div className="arch-row arch-compare" role="row" key={c.label}>
              <strong role="rowheader">{c.label}</strong>
              <span role="cell" className="muted">{c.naive}</span>
              <span role="cell">{c.hybrid}</span>
            </div>
          ))}
        </div>
        <p className="muted arch-small">
          Example: asked about invoice <code>INV-7731</code>, vector search ranked the right chunk 2nd, keyword search
          ranked it 1st, and the fused result kept it 1st.
        </p>
      </section>

      <SessionSection rag="hybrid" />
    </div>
  )
}
