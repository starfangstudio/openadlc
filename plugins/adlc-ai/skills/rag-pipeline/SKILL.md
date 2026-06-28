---
name: rag-pipeline
description: >-
  This skill should be used when the user asks to "add RAG to my app", "build a retrieval
  pipeline", "set up a vector store", "add document search over my knowledge base",
  "implement retrieval-augmented generation", "wire embeddings for semantic search",
  "add BM25 + vector hybrid retrieval", "rerank retrieved chunks", "improve RAG answer
  quality", "evaluate retrieval recall", "add citation grounding to LLM answers", "choose
  between pgvector and Pinecone", "chunk documents for embedding", "pick an embedding
  model", or "add faithfulness evals for my RAG". Covers the full pipeline: detect first,
  decide whether RAG is warranted, chunk, embed, store, retrieve (hybrid BM25 + vector),
  rerank, cite, and evaluate (retrieval recall + answer faithfulness).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# RAG pipeline

Build or extend a retrieval-augmented generation pipeline: chunk, embed, store, retrieve,
rerank, cite, and evaluate. Integrate only what the problem warrants -- over-engineering a
small corpus with managed vector infra is a failure mode, not a feature.

## Step 0: Decide whether RAG is warranted

**If the corpus fits in the model's context window, stuff it directly and skip this skill.**

Rules of thumb for "just stuff context":
- Fewer than ~50 documents or ~200k tokens total: pass everything as context.
- No need for source citation or provenance.
- Corpus is static and known at prompt-construction time.

RAG adds indexing latency, embedding cost, retrieval error modes, and eval overhead. Earn
every piece of that complexity.

## Step 1: Detect first

Never assume what already exists. Inspect before creating anything:

```bash
# Existing vector store or retrieval library
grep -rIl --include="*.py" --include="*.kt" --include="*.ts" \
  -e 'pgvector' -e 'sqlite.vec' -e 'sqlite_vec' -e 'chromadb' \
  -e 'qdrant' -e 'pinecone' -e 'weaviate' -e 'lancedb' \
  -e 'faiss' -e 'annoy' . | head

# Existing embedding calls
grep -rIn --include="*.py" --include="*.kt" --include="*.ts" \
  -e 'embeddings' -e 'embed(' -e 'create_embedding' . | head

# Existing chunking / ingestion scripts
find . -name "ingest*" -o -name "chunk*" -o -name "index*" | grep -v node_modules | head

# BM25 / full-text search already wired
grep -rIl --include="*.py" --include="*.kt" --include="*.ts" \
  -e 'BM25' -e 'bm25' -e 'rank_bm25' -e 'to_tsvector' . | head
```

Record: existing store, embedding library, chunk size, retrieval strategy. Mark anything
you cannot determine `unknown`; ask before inventing.

## Step 2: Chunking strategy

Choose a strategy matched to document type. Apply detected project conventions if any.
For the full strategy table and overlap/metadata guidance, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

Heuristic: target 256--512 tokens per chunk, ~10% overlap. Tune against recall@5 eval.
Store `doc_id`, `chunk_index`, `source_url`, `created_at` on every chunk.

## Step 3: Embedding model choice

Use the built-in `claude-api` skill for current model IDs and pricing. Prefer a
well-benchmarked open model; match embedding dimension to the store's index and hold it.
For on-device / mobile RAG, use quantized local models to keep user data on-device.
For model options and dimension guidance, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

## Step 4: Vector store selection

Pick the cheapest option your scale and ops posture can support. Key signal: already on
Postgres -> `pgvector`; local-first -> `sqlite-vec`; >1M vectors or no infra -> managed.
For the full decision table, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

## Step 5: Retrieval -- hybrid BM25 + vector + reranking

Plain vector search misses exact keywords; plain BM25 misses semantic equivalents. Use
both, fused with Reciprocal Rank Fusion, then re-score with a cross-encoder reranker.
Typical starting values: K1=20, K2=20, reranker top-N=5. Skip the reranker only when
recall@5 > 0.90. For the pipeline diagram and reranker options, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

## Step 6: Citation and grounding

Every chunk passed to the LLM must carry its `source_url` (or `doc_id` + `chunk_index`).
Instruct the model to cite inline and refuse to answer from parametric memory; a claim
with no `[source_N]` is a grounding failure. For the exact system prompt, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

## Step 7: Evaluation -- retrieval recall + answer faithfulness

Do not ship a RAG pipeline without a repeatable eval. Minimum two metrics:

- **Retrieval recall@K**: fraction of expected docs in top-K for a labeled test set.
  Target: recall@5 >= 0.80 before wiring to the LLM.
- **Answer faithfulness** (via RAGAS or equivalent): LLM-as-judge checks every claim
  against retrieved context. Target: faithfulness >= 0.85.

Build a labeled golden set of at least 50 (query, expected_doc_ids, expected_answer)
tuples. Re-run on every chunking or retrieval parameter change; log metric values.
Do not claim done without a passing eval run. For the RAGAS install and eval script, see [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md).

## Guardrails

- Corpus quality gates output quality. Stale, duplicate, or low-signal documents degrade
  faithfulness regardless of retrieval sophistication. Clean the corpus first.
- Never index PII without an explicit data-retention decision from the operator.
- Do not embed and store user query text server-side without consent (it is behavioral
  data). Cache only with explicit opt-in.
- If recall@5 is below 0.60 after tuning chunk size and hybrid retrieval, the problem is
  likely corpus quality or query--document mismatch, not the retrieval algorithm.

## Outbound checkpoint

Local work needs no approval. Outbound here (sending document chunks to an external embedding API such as OpenAI/Voyage/Cohere, sending queries or retrieved chunks to an external LLM API for answer generation or eval, writing chunk data to a managed vector store such as Pinecone/Qdrant Cloud/Weaviate Cloud, pushing the pipeline code or index artifacts to a remote repository): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- "Searching for Best Practices in Retrieval-Augmented Generation" (arXiv 2407.01219):
  https://arxiv.org/abs/2407.01219
- "A Hybrid Retrieval and Reranking Framework for Evidence-Grounded RAG" (arXiv 2605.01664):
  https://arxiv.org/abs/2605.01664
- RAGAS -- Automated Evaluation of RAG (arXiv 2309.15217):
  https://arxiv.org/abs/2309.15217
- RAGAS evaluation metrics (Confident AI, 2025):
  https://www.confident-ai.com/blog/rag-evaluation-metrics-answer-relevancy-faithfulness-and-more
- pgvector vs sqlite-vec comparison (2026):
  https://llbbl.blog/2026/04/26/pgvector-vs-sqlitevec-you-probably.html
- Vector database comparison 2026 (4xxi):
  https://4xxi.com/articles/vector-database-comparison/
- RAG advanced retrieval patterns 2026 (DEV Community):
  https://dev.to/young_gao/rag-is-not-dead-advanced-retrieval-patterns-that-actually-work-in-2026-2gbo
- Full implementation detail (chunking table, embedding options, store selection table,
  retrieval diagram, citation prompt, RAGAS script):
  [references/rag-pipeline-detail.md](references/rag-pipeline-detail.md)
