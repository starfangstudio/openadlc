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
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# RAG pipeline

Build or extend a retrieval-augmented generation pipeline: chunk, embed, store, retrieve,
rerank, cite, evaluate. Integrate only what the problem warrants. Over-engineering a small
corpus with managed vector infra is a failure mode, not a feature. Every step has an inline
executable minimum plus a pointer to `../../references/rag-pipeline-detail.md` for the full
version.

## Step 0: Decide whether RAG is warranted (gate)

**If the corpus fits in the model's context window, stuff it directly and skip this skill.**
Prefer full-context or file search when any of these hold: fewer than ~50 documents or under
~200k tokens total (pass everything as context); no need for source citation or provenance;
corpus is static and known at prompt-construction time.

RAG adds indexing latency, embedding cost, retrieval error modes, and eval overhead. Earn
every piece of it. For context-window sizes and prompt-caching economics, use `claude-api`.

## Step 1: Detect first

Never assume what exists. Inspect before creating anything:
```bash
grep -rIl -e 'pgvector' -e 'sqlite.vec' -e 'sqlite_vec' -e 'chromadb' -e 'qdrant' \
  -e 'pinecone' -e 'weaviate' -e 'lancedb' -e 'faiss' --include="*.py" --include="*.kt" --include="*.ts" . | head
grep -rIn -e 'embeddings' -e 'embed(' -e 'create_embedding' --include="*.py" --include="*.ts" . | head
find . -name "ingest*" -o -name "chunk*" -o -name "index*" | grep -v node_modules | head
grep -rIl -e 'BM25' -e 'bm25' -e 'rank_bm25' -e 'to_tsvector' . | head   # existing full-text/keyword search
```
Record the existing store, embedding library, chunk size, retrieval strategy. Mark anything
undetermined `unknown` and ask before inventing.

## Step 2: Chunking

Match strategy to document type. Apply detected project conventions if any exist.

| Document type | Strategy | Size / overlap |
|---|---|---|
| Prose / markdown | Recursive character split on headings then paragraphs | 512 tokens, ~10% overlap |
| Code | Split on function/class boundaries, never mid-symbol | logical unit, no fixed size |
| Structured (JSON, tables) | Serialize per-row or per-object, never mid-row | one row/object per chunk |
| PDF with layout | Page-aware split, strip headers/footers first | 512 tokens, ~10% overlap |

Target 256-512 tokens: smaller raises precision and lowers recall, larger does the reverse.
Overlap ~10% (25-50 tokens) stops sentences fragmenting across boundaries; tune against the
Step 7 recall eval. Store on every chunk: `doc_id`, `chunk_index`, `source_url`,
`created_at`. Retrieval without provenance cannot cite. Full guidance:
`../../references/rag-pipeline-detail.md`.

## Step 3: Embedding model

Start with a well-benchmarked, cheap model before paying for larger ones (a small hosted
embedding model, or local `nomic-embed-text` via Ollama for on-device). Match the embedding
dimension to the store's index (768 or 1536 are common) and hold it: re-indexing on a
dimension change is expensive. For on-device/mobile RAG use a quantized local model to keep
data on-device. Use the `claude-api` skill for current model IDs and pricing, do not
hardcode them. Options: `../../references/rag-pipeline-detail.md`.

## Step 4: Vector store

Pick the cheapest option your scale and ops posture support.

| Signal | Choice |
|---|---|
| Postgres already in the stack, scale modest (< ~1M vectors) | `pgvector` extension, zero new infra |
| Local / edge / embedded (CLI, desktop, mobile), small corpus | `sqlite-vec`, single `.db` file, no daemon |
| > ~1M vectors, or p95 latency / multi-tenant / no-ops-team demands | managed (Pinecone, Qdrant Cloud, Weaviate Cloud) |

Managed stores cost roughly 5-10x self-hosted per vector; only pay when you genuinely cannot
run the infra. Threshold signals: vector count, required p95 latency, multi-tenant isolation,
whether a team can run a daemon. Detail: `../../references/rag-pipeline-detail.md`.

## Step 5: Retrieval (hybrid BM25 + vector, rerank when it earns its cost)

Plain vector search misses exact keywords; plain BM25 misses semantic equivalents. Run both,
fuse with Reciprocal Rank Fusion (`RRF = sum 1/(k+rank)`, k=60; merge + dedup), then
optionally re-score the fused top-N with a cross-encoder reranker before sending top-K to the
LLM. Starting values: BM25 K1=20, vector K2=20, reranker top-N=5. **Add the reranker only
when it earns its cost:** skip it while recall@5 already exceeds 0.90 (Step 7), since it adds
latency and (for a hosted one) per-call cost. Cheapest first: local
`cross-encoder/ms-marco-MiniLM-L-6-v2`, then stronger local `bge-reranker-v2-m3` via Ollama,
then a hosted rerank API. Tuning: `../../references/rag-pipeline-detail.md`.

## Step 6: Citation and grounding (the prompt rule)

Every chunk passed to the LLM must carry its `source_url` (or `doc_id` + `chunk_index`). The
answer must cite the retrieved chunk ids it used and must refuse when retrieval is empty.
```
System: Answer using ONLY the provided context. After each claim, append [source_N] naming
        the chunk id it came from. If the context is empty or does not support the answer,
        reply exactly "I don't know." Do not answer from prior knowledge.
```
A claim with no `[source_N]` is a grounding failure; empty retrieval must refuse, never guess.
Exact prompt: `../../references/rag-pipeline-detail.md`.

## Step 7: Evaluation (do not ship without a passing run)

Two gated metrics: **retrieval recall@5 >= 0.80** (fraction of expected docs in top-5 over a
labeled set) before wiring to the LLM, and **answer faithfulness >= 0.85** (RAGAS or
equivalent LLM-as-judge, checks every claim against retrieved context). Runnable recipe:
```bash
pip install ragas datasets            # then build a golden set, 10-20 rows min (grow to ~50)
```
Golden row shape, one per line: `{"question": "...", "expected_doc_ids": ["d12#3"], "ground_truth": "..."}`
```python
# eval.py -- exits non-zero if either target is missed
from ragas import evaluate
from ragas.metrics import faithfulness, context_recall
r = evaluate(dataset, metrics=[faithfulness, context_recall])  # dataset = golden rows + retriever/LLM outputs
assert r["context_recall"] >= 0.80 and r["faithfulness"] >= 0.85, dict(r)
print("PASS", dict(r))
```
Re-run on every chunking or retrieval-parameter change and log the values. Do not claim done
without a passing run. Full script: `../../references/rag-pipeline-detail.md`.

## Guardrails (honesty)

- Corpus quality gates output quality. Stale, duplicate, or low-signal docs degrade
  faithfulness regardless of retrieval sophistication. Clean the corpus first.
- Never index PII without an explicit data-retention decision from the operator. Do not
  embed or store user query text server-side without consent (it is behavioral data): cache
  only on explicit opt-in.
- If recall@5 stays below 0.60 after tuning chunk size and hybrid retrieval, the problem is
  almost certainly corpus quality or query-document mismatch, not the retrieval algorithm.
- This skill improves grounding, it cannot guarantee correctness. A passing eval bounds the
  error rate on the golden set, it does not certify unseen queries.

## Outbound checkpoint

Local work needs no approval. Outbound here (sending chunks to an external embedding API,
sending queries or retrieved chunks to an external LLM for generation or eval, writing to a
managed vector store, or pushing pipeline code / index artifacts to a remote): stop, present
exactly what would go out, get the operator's explicit "yes" first (global consent law).

## References

- Full implementation detail (all tables, retrieval diagram, citation prompt, RAGAS script):
  `../../references/rag-pipeline-detail.md`
- pgvector, official extension repo/docs: https://github.com/pgvector/pgvector
- sqlite-vec, official extension repo/docs: https://github.com/asg017/sqlite-vec
- RAGAS: Automated Evaluation of RAG (arXiv 2309.15217): https://arxiv.org/abs/2309.15217
- Reciprocal Rank Fusion (Cormack, Clarke, Buettcher, SIGIR 2009): the RRF score used above.
- "Searching for Best Practices in RAG" (arXiv 2407.01219): https://arxiv.org/abs/2407.01219
- Managed stores: cite the vendor's own docs (Pinecone / Qdrant / Weaviate) for current
  limits and pricing, not third-party comparison blogs. Model IDs and embedding pricing:
  `claude-api` skill.
