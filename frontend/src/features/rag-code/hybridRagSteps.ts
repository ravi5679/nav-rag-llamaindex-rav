// Content of the Hybrid RAG "Step-by-Step Code" tab.
// Steps 1-7 are the same as Naive RAG; only retrieval changes (backend/rag_steps/hybrid_retriever.py).
// The full script (last step) was run end to end against the versions below.
import { naiveLibraries, naiveSteps, type CodeStep, type Library } from './naiveRagSteps'

export const hybridLibraries: Library[] = naiveLibraries.map((l) =>
  l.name === 'lancedb' ? { ...l, usedFor: 'The vector database, and its full-text (BM25) search for keywords' } : l,
)

const sameAsNaive = (id: string): CodeStep => {
  const step = naiveSteps.find((s) => s.id === id)
  if (!step) throw new Error(`unknown step ${id}`)
  return { ...step, summary: `Same as Naive RAG. ${step.summary}` }
}

export const hybridSteps: CodeStep[] = [
  {
    ...naiveSteps[0],
    summary: 'The same libraries as Naive RAG; no extra package is needed: LanceDB already has BM25 full-text search.',
  },
  {
    ...naiveSteps[1],
    summary: 'Same CONFIG as Naive RAG, plus how many candidates each of the two searches returns.',
    code: `import os
from dotenv import load_dotenv

load_dotenv()  # puts .env values into os.environ

CONFIG = {
    "llm": {"model": os.getenv("LLM_MODEL", "gpt-4o-mini"), "temperature": 0.1},
    "embeddings": {
        "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
    },
    "vector_store": {"path": "storage/lancedb", "table_name": "documents"},
    "index": {"storage_path": "storage/index", "similarity_top_k": 4},   # chunks sent to the LLM
    "hybrid": {
        "vector_top_k": int(os.getenv("HYBRID_VECTOR_TOP_K", "5")),    # candidates from vector search
        "keyword_top_k": int(os.getenv("HYBRID_KEYWORD_TOP_K", "5")),  # candidates from keyword search
    },
}


def get_config(key_path: str, default_value=None):
    """get_config("hybrid.vector_top_k") -> 5"""
    value = CONFIG
    for key in key_path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default_value
    return value`,
  },
  sameAsNaive('settings'),
  sameAsNaive('vector-store'),
  sameAsNaive('load'),
  sameAsNaive('chunk'),
  sameAsNaive('embed'),
  sameAsNaive('index'),
  {
    id: 'retrievers',
    title: 'Step 8 · Two retrievers: meaning + keywords',
    summary:
      'Both search the SAME LanceDB table. The vector retriever finds similar meaning; the keyword retriever uses LanceDB full-text search, ranked with BM25, to find exact words like codes, IDs and names.',
    libraries: ['llama-index-core', 'lancedb'],
    file: 'backend/rag_steps/hybrid_retriever.py',
    lang: 'python',
    code: `from llama_index.core.retrievers import VectorIndexRetriever

# Meaning: embed the question, find the closest chunk vectors
vector_retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=get_config("hybrid.vector_top_k"),
)

# Exact words: LanceDB full-text search (BM25) on the chunk text.
# LanceDB builds the full-text index automatically on first use.
keyword_retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=get_config("hybrid.keyword_top_k"),
    vector_store_kwargs={"query_type": "fts"},
)`,
  },
  {
    id: 'fusion',
    title: 'Step 9 · Fuse with Reciprocal Rank Fusion',
    summary:
      'QueryFusionRetriever runs both retrievers and merges their rankings: each chunk scores the sum of 1/(60 + rank) over the lists, so chunks that rank well in both win. Only ranks are used, so the different score scales don’t matter.',
    libraries: ['llama-index-core'],
    file: 'backend/rag_steps/hybrid_retriever.py',
    lang: 'python',
    code: `from llama_index.core.retrievers import QueryFusionRetriever

hybrid_retriever = QueryFusionRetriever(
    [vector_retriever, keyword_retriever],
    mode="reciprocal_rerank",                              # Reciprocal Rank Fusion
    similarity_top_k=get_config("index.similarity_top_k"),  # final chunks for the LLM (4)
    num_queries=1,     # use the question as-is (>1 asks the LLM to write extra queries)
    use_async=True,    # run both searches at the same time
)

for node in hybrid_retriever.retrieve("Which customer is invoice INV-7731 for?"):
    print(round(node.score, 3), node.get_content()[:80])`,
  },
  {
    id: 'query',
    title: 'Step 10 · Query engine',
    summary: 'Exactly like Naive RAG, but the query engine wraps the hybrid retriever instead of the vector retriever.',
    libraries: ['llama-index-core', 'llama-index-llms-openai'],
    file: 'backend/rag_steps/query_engine.py',
    lang: 'python',
    code: `from llama_index.core.query_engine import RetrieverQueryEngine

query_engine = RetrieverQueryEngine.from_args(retriever=hybrid_retriever)   # uses Settings.llm

response = query_engine.query("Which customer is invoice INV-7731 for?")
print(response)
for source in response.source_nodes:
    print(source.metadata["file_name"], round(source.score, 3))   # fused RRF scores (small numbers)`,
  },
  {
    id: 'full',
    title: 'Everything together · hybrid_rag.py',
    summary: 'All steps in one runnable file. Put files in ./data and run it: the first run ingests, later runs load the saved index.',
    libraries: ['llama-index-core', 'lancedb', 'python-dotenv'],
    file: 'backend/hybrid_rag/pipeline.py (the API version, with sessions)',
    lang: 'python',
    code: `"""Hybrid RAG in one file: LlamaIndex + OpenAI + LanceDB (vector + BM25 keyword search).
Put a few files in ./data, set OPENAI_API_KEY in .env, then run:  python hybrid_rag.py
"""
import os

from dotenv import load_dotenv
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import QueryFusionRetriever, VectorIndexRetriever
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.lancedb import LanceDBVectorStore

# ---------- Step 1: configuration ----------
load_dotenv()
CONFIG = {
    "llm": {"model": "gpt-4o-mini", "temperature": 0.1},
    "embeddings": {"model": "text-embedding-3-small", "chunk_size": 512, "chunk_overlap": 50},
    "vector_store": {"path": "storage/lancedb", "table_name": "documents"},
    "index": {"storage_path": "storage/index", "similarity_top_k": 4},
    "hybrid": {"vector_top_k": 5, "keyword_top_k": 5},
    "documents": {"folder": "data"},
}

# ---------- Step 2: LlamaIndex settings ----------
Settings.llm = OpenAI(model=CONFIG["llm"]["model"], temperature=CONFIG["llm"]["temperature"])
Settings.embed_model = OpenAIEmbedding(model=CONFIG["embeddings"]["model"])

# ---------- Step 3: vector store ----------
vector_store = LanceDBVectorStore(
    uri=CONFIG["vector_store"]["path"], table_name=CONFIG["vector_store"]["table_name"]
)
index_path = CONFIG["index"]["storage_path"]

if os.path.exists(os.path.join(index_path, "index_store.json")):
    # Already ingested: load the saved index (no re-embedding)
    storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=index_path)
    index = load_index_from_storage(storage_context, store_nodes_override=True)
else:
    # ---------- Steps 4-7: load, chunk, embed, store + index (same as Naive RAG) ----------
    documents = SimpleDirectoryReader(CONFIG["documents"]["folder"]).load_data()
    splitter = SentenceSplitter(
        chunk_size=CONFIG["embeddings"]["chunk_size"],
        chunk_overlap=CONFIG["embeddings"]["chunk_overlap"],
    )
    chunks = splitter.get_nodes_from_documents(documents)
    texts = [c.get_content(metadata_mode=MetadataMode.EMBED) for c in chunks]
    for chunk, vector in zip(chunks, Settings.embed_model.get_text_embedding_batch(texts)):
        chunk.embedding = vector
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes=chunks, storage_context=storage_context, store_nodes_override=True)
    storage_context.persist(persist_dir=index_path)
    print(f"Indexed {len(documents)} documents as {len(chunks)} chunks")

# ---------- Step 8: two retrievers over the same LanceDB table ----------
vector_retriever = VectorIndexRetriever(        # meaning
    index=index, similarity_top_k=CONFIG["hybrid"]["vector_top_k"]
)
keyword_retriever = VectorIndexRetriever(       # exact words: LanceDB full-text search (BM25)
    index=index,
    similarity_top_k=CONFIG["hybrid"]["keyword_top_k"],
    vector_store_kwargs={"query_type": "fts"},
)

# ---------- Step 9: fuse both rankings (Reciprocal Rank Fusion) ----------
hybrid_retriever = QueryFusionRetriever(
    [vector_retriever, keyword_retriever],
    mode="reciprocal_rerank",
    similarity_top_k=CONFIG["index"]["similarity_top_k"],
    num_queries=1,       # use the question as-is
    use_async=False,     # simple synchronous script
)

# ---------- Step 10: query engine + ask ----------
query_engine = RetrieverQueryEngine.from_args(retriever=hybrid_retriever)
response = query_engine.query("Which customer is invoice INV-7731 for?")
print(response)
for source in response.source_nodes:
    print(f"- {source.metadata.get('file_name')} (fused score {source.score:.3f})")`,
  },
]
