"""Naive RAG steps, one file each. Functions take everything as arguments,
so these files don't depend on any particular app's config.

  Setup   llamaindex_settings.py  configure the LLM and embedding model (Step 2)
          vector_store.py         create / check / clear the LanceDB vector store

  Ingest  load_documents.py       Upload: read saved files into Documents
          chunk_documents.py      Chunk: SentenceSplitter
          embed_chunks.py         Embedding: one vector per chunk
          vector_index.py         Vector DB + indexing: LanceDB + saved index

  Query   query_engine.py         retriever (top-k) + LLM that answers questions

(Step 1, configuration, belongs to the app using these steps.)
"""
