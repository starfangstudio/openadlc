<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `rag-pipeline` skill. Load on demand; do not load independently.

---

## Chunking strategy by document type

| Document type | Strategy |
|---|---|
| Prose / markdown | Recursive character split, 512 tokens, 10% overlap |
| Code | Split on function/class boundaries, not character count |
| Structured (JSON, tables) | Serialize per-row or per-object; do not mid-row split |
| PDFs with layout | Page-aware split; strip headers/footers before chunking |

- Target 256--512 tokens per chunk. Smaller = higher precision, lower recall; larger = vice versa. Tune with retrieval-recall eval.
- Overlap at ~10% (25--50 tokens) prevents sentence fragmentation across chunk boundaries.
- Store chunk metadata: `doc_id`, `chunk_index`, `source_url`, `created_at`. Retrieval without provenance cannot produce citations.

---

## Embedding model guidance

- Start with a well-benchmarked open model (e.g., `text-embedding-3-small` from OpenAI, `voyage-3-lite` from Voyage AI, or a local `nomic-embed-text` via Ollama) before paying for larger models.
- Match embedding dimension to the store's index (768 or 1536 are common; pick one and hold it -- re-indexing on dimension change is expensive).
- For on-device / mobile RAG: quantized local models (e.g., MLC-LLM, llama.cpp with GGUF embeddings) avoid network round-trips and keep user data on-device.

Use the built-in `claude-api` skill for current model IDs and pricing; do not hardcode them.

---

## Vector store selection

| Scenario | Recommendation |
|---|---|
| Already on Postgres | `pgvector` extension -- zero new infra |
| Local-first / embedded (CLI, desktop, mobile) | `sqlite-vec` -- single `.db` file, no daemon |
| <1M vectors, team manages infra | `pgvector` or `Qdrant` self-hosted |
| >1M vectors or fully managed required | Pinecone or Qdrant Cloud |

Managed services cost 5--10x self-hosted per token stored; only pay if you genuinely cannot manage the infra.

---

## Hybrid retrieval pipeline and reranker options

```
query
  -> BM25 sparse retrieval   (top-K1 by keyword score)
  -> Vector dense retrieval  (top-K2 by cosine/dot similarity)
  -> Reciprocal Rank Fusion  (merge, deduplicate)
  -> Cross-encoder reranker  (re-score top-N for true relevance)
  -> top-K final chunks -> LLM prompt
```

Typical starting values: K1=20, K2=20, reranker top-N=5. Tune against recall@5 eval.

Reranker options (in cost order):
1. `cross-encoder/ms-marco-MiniLM-L-6-v2` (local, fast, free)
2. Cohere Rerank API (managed, pays per call)
3. `bge-reranker-v2-m3` via Ollama (local, stronger)

Skip the reranker only when retrieval recall@5 already exceeds 0.90 in eval.

---

## Citation system prompt

```
System: Answer using ONLY the provided context. For each claim, append [source_N].
        If the context does not support the answer, say "I don't know."
```

Every chunk passed to the LLM must carry its `source_url` (or `doc_id` + `chunk_index`). A claim with no `[source_N]` is a grounding failure.

---

## RAGAS evaluation setup

```bash
# Install RAGAS
pip install ragas

# Minimal eval script shape (fill in your retriever + LLM)
# from ragas import evaluate
# from ragas.metrics import faithfulness, context_recall
# result = evaluate(dataset, metrics=[faithfulness, context_recall])
# assert result["context_recall"] >= 0.80
# assert result["faithfulness"] >= 0.85
```

Build a labeled golden set of at least 50 (query, expected_doc_ids, expected_answer) tuples. Re-run eval on every chunking or retrieval parameter change.
