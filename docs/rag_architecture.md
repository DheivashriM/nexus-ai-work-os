# RAG (Retrieval-Augmented Generation) Architecture Specification

## Purpose & Scope
RAG will be added in Phase 2 for semantic discovery across static company documentation, BRDs, PRDs, SOPs, policies, meeting transcripts, and client communications.

> [!IMPORTANT]
> **Strict Operational Boundary**:
> RAG must **NEVER** be used to retrieve live operational data (e.g. current task status, assigned user, active blockers). Operational data is queried synchronously from PostgreSQL via backend service endpoints.

## Proposed RAG Pipeline

```
Company Documents / Transcripts / Policy PDFs
                   │
                   ▼
  Text Extraction & Chunking (LangChain / LlamaIndex)
                   │
                   ▼
  Embedding Model (OpenAI text-embedding-3-small / Cohere / HuggingFace)
                   │
                   ▼
  Vector Database (pgvector / Qdrant / Pinecone)
                   │
                   ▼
  Semantic Retrieval via Agent Tool (`search_documents`)
```

## Data Separation
- **PostgreSQL Operational Schema**: `users`, `projects`, `tasks`, `blockers`, `activities`, `notifications`.
- **pgvector Vector Store Schema**: `document_embeddings` (id, document_id, chunk_index, content, embedding_vector, metadata).
