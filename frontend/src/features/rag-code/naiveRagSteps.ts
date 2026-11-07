// Content of the Naive RAG "Step-by-Step Code" tab.
// Snippets are simplified from backend/rag_steps/*.py; keep them in sync when those change.
// The full script (last step) was run end to end against the versions below.

export interface Library {
  name: string
  version: string
  usedFor: string
}

export interface CodeStep {
  id: string
  title: string
  summary: string
  libraries: string[]
  file: string // where the real version lives in this project
  lang: 'python' | 'bash'
  code: string
}

export const naiveLibraries: Library[] = [
  { name: 'llama-index-core', version: '0.14.25', usedFor: 'Documents, SentenceSplitter, VectorStoreIndex, retriever, query engine' },
  { name: 'llama-index-llms-openai', version: '0.7.10', usedFor: 'OpenAI chat model that writes the answer (gpt-4o-mini)' },
  { name: 'llama-index-embeddings-openai', version: '0.6.0', usedFor: 'OpenAI embedding model (text-embedding-3-small)' },
  { name: 'llama-index-vector-stores-lancedb', version: '0.6.0', usedFor: 'Connects LlamaIndex to LanceDB' },
  { name: 'lancedb', version: '0.40.0', usedFor: 'The vector database: a folder on disk, no server' },
  { name: 'llama-index-readers-file', version: '0.7.0', usedFor: 'PDF / DOCX readers used by SimpleDirectoryReader' },
  { name: 'python-dotenv', version: '1.2.4', usedFor: 'Loads OPENAI_API_KEY and settings from .env' },
]

export const naiveSteps: CodeStep[] = [
  {
    id: 'install',
    title: 'Install the libraries',
    summary: 'One command installs LlamaIndex, the OpenAI integrations and LanceDB. Put your OpenAI key in a .env file.',
    libraries: ['uv'],
    file: 'backend/pyproject.toml',
    lang: 'bash',
    code: `uv add llama-index llama-index-llms-openai llama-index-embeddings-openai \\
       llama-index-vector-stores-lancedb llama-index-readers-file \\
       lancedb python-dotenv

# .env
OPENAI_API_KEY=sk-your-key`,
  },
  {
    id: 'config',
    title: 'Step 1 · Configuration',
    summary: 'Every setting lives in one CONFIG dictionary, read with dot notation. Values come from .env, with defaults.',
    libraries: ['python-dotenv'],
    file: 'backend/common/config.py',
    lang: 'python',
    code: `import os
from dotenv import load_dotenv

load_dotenv()  # puts .env values into os.environ

CONFIG = {
    "llm": {
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "temperature": float(os.getenv("TEMPERATURE", "0.1")),
    },
    "embeddings": {
        "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
    },
    "vector_store": {"path": "storage/lancedb", "table_name": "documents"},
    "index": {"storage_path": "storage/index", "similarity_top_k": 4},
}


def get_config(key_path: str, default_value=None):
    """get_config("llm.model") -> "gpt-4o-mini" """
    value = CONFIG
    for key in key_path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default_value
    return value`,
  },
  {
    id: 'settings',
    title: 'Step 2 · LlamaIndex Settings',
    summary: 'Set the LLM and embedding model once. Every later step (index, retriever, query engine) uses them automatically.',
    libraries: ['llama-index-llms-openai', 'llama-index-embeddings-openai'],
    file: 'backend/rag_steps/llamaindex_settings.py',
    lang: 'python',
    code: `from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# LLM: writes the final answer from the retrieved chunks
Settings.llm = OpenAI(
    model=get_config("llm.model"),
    temperature=get_config("llm.temperature"),   # low = factual
)

# Embedding model: text -> vector. Documents and questions MUST use the same one.
Settings.embed_model = OpenAIEmbedding(model=get_config("embeddings.model"))`,
  },
  {
    id: 'vector-store',
    title: 'Step 3 · Vector store (LanceDB)',
    summary: 'LanceDB stores each chunk’s text, metadata and vector in a folder on disk. The table is created on the first insert.',
    libraries: ['lancedb', 'llama-index-vector-stores-lancedb'],
    file: 'backend/rag_steps/vector_store.py',
    lang: 'python',
    code: `from llama_index.vector_stores.lancedb import LanceDBVectorStore

vector_store = LanceDBVectorStore(
    uri=get_config("vector_store.path"),            # e.g. storage/lancedb
    table_name=get_config("vector_store.table_name"),
)`,
  },
  {
    id: 'load',
    title: 'Step 4 · Upload: load documents',
    summary: 'SimpleDirectoryReader picks the right parser per file type. A PDF becomes one Document per page, with metadata like file_name.',
    libraries: ['llama-index-core', 'llama-index-readers-file'],
    file: 'backend/rag_steps/load_documents.py',
    lang: 'python',
    code: `from llama_index.core import SimpleDirectoryReader

# A whole folder ...
documents = SimpleDirectoryReader("data", recursive=True).load_data()

# ... or specific files (what the API does after an upload)
documents = SimpleDirectoryReader(input_files=["data/report.pdf"]).load_data()

print(len(documents), documents[0].metadata["file_name"])`,
  },
  {
    id: 'chunk',
    title: 'Step 5 · Chunk with SentenceSplitter',
    summary: 'Split documents into small, focused chunks. SentenceSplitter breaks at sentence boundaries; the overlap keeps context at the edges.',
    libraries: ['llama-index-core'],
    file: 'backend/rag_steps/chunk_documents.py',
    lang: 'python',
    code: `from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(
    chunk_size=get_config("embeddings.chunk_size"),        # max tokens per chunk (512)
    chunk_overlap=get_config("embeddings.chunk_overlap"),  # tokens shared by neighbours (50)
)
chunks = splitter.get_nodes_from_documents(documents)   # each chunk keeps its file's metadata`,
  },
  {
    id: 'embed',
    title: 'Step 6 · Embedding',
    summary: 'Turn every chunk into a vector with the embedding model from Step 2. This is the step that calls OpenAI (and costs money).',
    libraries: ['llama-index-embeddings-openai'],
    file: 'backend/rag_steps/embed_chunks.py',
    lang: 'python',
    code: `from llama_index.core import Settings
from llama_index.core.schema import MetadataMode

texts = [c.get_content(metadata_mode=MetadataMode.EMBED) for c in chunks]
vectors = Settings.embed_model.get_text_embedding_batch(texts)   # batched OpenAI calls

for chunk, vector in zip(chunks, vectors):
    chunk.embedding = vector   # the index step won't embed these again`,
  },
  {
    id: 'index',
    title: 'Step 7 · Vector DB + indexing',
    summary: 'Write the embedded chunks to LanceDB and save the index (docstore + metadata) to disk. Next time, load it instead of re-embedding.',
    libraries: ['llama-index-core', 'llama-index-vector-stores-lancedb'],
    file: 'backend/rag_steps/vector_index.py',
    lang: 'python',
    code: `from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage

index_path = get_config("index.storage_path")   # e.g. storage/index

# Build: vectors go to LanceDB, the index itself is saved to index_path
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex(
    nodes=chunks,
    storage_context=storage_context,
    store_nodes_override=True,   # also keep every chunk in the saved docstore
)
storage_context.persist(persist_dir=index_path)

# Later (e.g. after a restart): load it back, no OpenAI calls
storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=index_path)
index = load_index_from_storage(storage_context, store_nodes_override=True)`,
  },
  {
    id: 'query',
    title: 'Step 8 · Query engine',
    summary: 'The retriever finds the top-k closest chunks; the query engine puts them and the question into a prompt for the LLM.',
    libraries: ['llama-index-core', 'llama-index-llms-openai'],
    file: 'backend/rag_steps/query_engine.py',
    lang: 'python',
    code: `from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever

retriever = VectorIndexRetriever(index=index, similarity_top_k=get_config("index.similarity_top_k"))
query_engine = RetrieverQueryEngine.from_args(retriever=retriever)   # uses Settings.llm

response = query_engine.query("What is this document about?")
print(response)                                  # the answer
for source in response.source_nodes:             # the chunks it was based on
    print(source.metadata["file_name"], round(source.score, 2))`,
  },
  {
    id: 'full',
    title: 'Everything together · naive_rag.py',
    summary: 'All steps in one runnable file. Put files in ./data and run it: the first run ingests, later runs load the saved index.',
    libraries: ['llama-index-core', 'lancedb', 'python-dotenv'],
    file: 'backend/naive_rag/pipeline.py (the API version, with sessions)',
    lang: 'python',
    code: `"""Naive RAG in one file: LlamaIndex + OpenAI + LanceDB.
Put a few files in ./data, set OPENAI_API_KEY in .env, then run:  python naive_rag.py
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
from llama_index.core.retrievers import VectorIndexRetriever
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
    # ---------- Step 4: load documents ----------
    documents = SimpleDirectoryReader(CONFIG["documents"]["folder"]).load_data()

    # ---------- Step 5: chunk ----------
    splitter = SentenceSplitter(
        chunk_size=CONFIG["embeddings"]["chunk_size"],
        chunk_overlap=CONFIG["embeddings"]["chunk_overlap"],
    )
    chunks = splitter.get_nodes_from_documents(documents)

    # ---------- Step 6: embed ----------
    texts = [c.get_content(metadata_mode=MetadataMode.EMBED) for c in chunks]
    for chunk, vector in zip(chunks, Settings.embed_model.get_text_embedding_batch(texts)):
        chunk.embedding = vector

    # ---------- Step 7: store in LanceDB + build and save the index ----------
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes=chunks, storage_context=storage_context, store_nodes_override=True)
    storage_context.persist(persist_dir=index_path)
    print(f"Indexed {len(documents)} documents as {len(chunks)} chunks")

# ---------- Step 8: query engine ----------
retriever = VectorIndexRetriever(index=index, similarity_top_k=CONFIG["index"]["similarity_top_k"])
query_engine = RetrieverQueryEngine.from_args(retriever=retriever)

# ---------- Step 9: ask ----------
response = query_engine.query("What is this document about?")
print(response)
for source in response.source_nodes:
    print(f"- {source.metadata.get('file_name')} (score {source.score:.2f})")`,
  },
]
