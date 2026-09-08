# Payments/Fintech RAG + Agent — v0.1 Build Plan

A retrieval-augmented, tool-using agent that answers questions over payments
documentation (SEPA rulebooks + ISO 20022 message specs), with citations, an
eval set, and your existing `fx-mcp-server` tools plugged in as agent tools.

> **Framing rule:** This plan is built backwards from a **3-week ship date**.
> The risk is not building the wrong thing — it's building forever. Every
> section has a cut line. If you catch yourself expanding one, that's the
> over-planning pattern. Ship v0.1, then improve in commits.

---

## 1. Definition of Done (the contract — do not move it)

v0.1 is done when it:

- [ ] Answers questions over **one** payments corpus, with **citations** (doc name + page/section).
- [ ] Runs an **agent loop** where Claude decides when to call tools:
  - `search_docs` (your RAG retrieval)
  - `convert` (from fx-mcp-server)
  - `validate_iban` (from fx-mcp-server)
- [ ] Has an **eval set** of ~25 Q&A pairs scored with Ragas (faithfulness + context precision/recall).
- [ ] Has a **README** with: architecture, chunking strategy, eval numbers, and 2–3 documented failure cases.
- [ ] Has a **runnable demo** — CLI or a ~40-line Streamlit UI — plus one screenshot/GIF.

If it does these, you ship and post. Everything past this line is v0.2.

---

## 2. Corpus decision (make it once, now)

**Choice: SEPA rulebooks + a few ISO 20022 payment message specs** (e.g. `pacs.008`, `pain.001`).

- Publicly available (European Payments Council / ISO 20022 publish them).
- Genuinely payments-domain — the moat.
- Bounded. **Cap at ~100–200 pages total. Download 3–5 PDFs, then stop.**

Why this over generic ECB/regulatory PDFs: a tool that answers *"which field in
pacs.008 carries structured remittance info?"* is unmistakably a payments
engineer's tool. Specificity is the differentiator.

**Copyright:** ingest for retrieval, cite sources, do **not** republish the PDFs
in the repo. Link to official sources in the README. Keep PDFs in a gitignored
`data/` folder.

---

## 3. Architecture

```
Query
  -> Agent loop (Claude, Anthropic tool-use API)
      |- tool: search_docs(query)       -> RAG retriever -> top-k chunks + citations
      |- tool: convert(src, dst, amount) -> fx-mcp-server
      |- tool: validate_iban(iban)       -> fx-mcp-server
  -> Claude composes a grounded answer with citations
```

The agent is just Claude with three tools. It reads a question, decides whether
it needs docs, math, or both, calls tools, and answers.

**The demo that sells it** (only possible because the fx tools already exist):

> "Validate IBAN DE89370400440532013000, convert 5000 EUR to USD at today's ECB
> rate, and tell me which pacs.008 field carries the amount."

Multi-tool composition in one query = the thing that makes a recruiter stop scrolling.

---

## 4. Stack (opinionated, minimal — don't shop for alternatives)

| Layer | Choice | Notes |
|---|---|---|
| Parsing | `pymupdf` (fitz) | One library; keeps page numbers for citations |
| Chunking | recursive / token-based | ~500 tokens, ~50 overlap. **No semantic chunking in v0.1** |
| Embeddings | one hosted model | OpenAI `text-embedding-3-small` (cheap) or Voyage `voyage-3`; local `bge-small` for zero cost. Pick in 5 min |
| Vector store | **Chroma**, local, file-backed | ~3 lines. pgvector is a v0.2 upgrade, not now |
| LLM / agent | Claude Sonnet (Anthropic API) | Native tool-use |
| Eval | **Ragas** | RAG-focused standard: faithfulness, answer_relevancy, context_precision, context_recall. Reference-light |
| UI | CLI first | Streamlit only if there's a spare evening |

### File layout

```
src/
  ingest.py      # parse PDFs -> chunk -> embed -> store in Chroma
  retriever.py   # search_docs(query) -> chunks + citations
  agent.py       # Claude tool-use loop; wires search_docs + fx tools
  tools.py       # tool schemas
eval/
  qa_set.jsonl   # ~25 question/answer/ground-truth-context rows
  run_eval.py    # Ragas scoring -> prints/saves metrics table
data/            # gitignored: PDFs, chroma db
README.md
```

---

## 5. The 3-Week Plan (evenings)

### Week 1 — Retrieval that works
- **Day 1–2:** Download corpus. Write `ingest.py`: parse -> chunk -> embed -> Chroma. Verify chunk count and that page numbers survive.
- **Day 3–4:** `retriever.py`: `search_docs(query)` returns top-k chunks with `{doc, page, text}`. Test by hand with 5 questions — eyeball whether the right chunks come back. **This is the make-or-break step.** If retrieval is junk, nothing downstream matters. Tune `k` and chunk size *here, nowhere else*.
- **Day 5:** Wrap retrieval in a Claude call that answers *with citations only from retrieved chunks*.
  - **Milestone:** ask a payments question, get a cited answer.

### Week 2 — Agent + evals
- **Day 1–2:** `agent.py` — Anthropic tool-use loop. Register `search_docs`. Get the model reliably calling it and composing an answer. **Cap loop iterations** — never-terminating tool-use loops are the classic bug.
- **Day 3:** Wire in `convert` and `validate_iban`. Test the multi-tool query.
  - **Milestone:** the impressive demo works.
- **Day 4–5:** Build `eval/qa_set.jsonl` — 25 real questions written from the corpus. Tedious, and the step people skip; also the step that separates you from every demo-only portfolio. Wire `run_eval.py` with Ragas. Get first faithfulness / context-precision numbers.

### Week 3 — Make it legible (equal weight to the code)
- **Day 1:** Read eval numbers. Fix the **one** worst thing (usually chunk size or `k`). Re-run. Don't chase perfection — document the number as-is.
- **Day 2:** Write 2–3 honest failure cases (e.g. "multi-hop questions across two rulebooks fail because retrieval only pulls one").
- **Day 3–4:** README — architecture diagram, chunking rationale, eval table, failure cases, "future work." One screenshot/GIF of the multi-tool demo.
- **Day 5:** Push. Post. **Ship.**

---

## 6. The writeup is half the grade

Two engineers build the same system; the one who writes *"here's my chunking
strategy, faithfulness = 0.82, here's what fails and why"* gets the interview.
Recruiters skim code but read READMEs. Budget Week 3 as seriously as Week 1.
Honest (not perfect) eval numbers are themselves a credibility signal — they say
you know how to measure, the exact Applied-AI skill teams lack.

---

## 7. Do NOT build in v0.1 (the fence)

Hybrid search, reranking, semantic chunking, pgvector, Pinecone, multi-corpus,
a React frontend, auth, conversation memory, streaming UI, Docker/deploy,
fine-tuning.

Every one is a legitimate v0.2 line item **and** a legitimate excuse to never
ship. Put them in the README's "future work" — that signals you know about them
without having to build them.

---

## 8. Risk / outcome

- **Biggest risk:** Week 1 retrieval "not good enough" becomes a rabbit hole, OR the eval-set authoring (Week 2, Day 4–5) feels boring so you skip it and build another feature instead. Both are the pattern. **The eval set is the highest-leverage, most-skipped, most-impressive part — protect it.**
- **Most likely outcome if you follow this:** a differentiated portfolio anchor in 3 weeks that maps 1:1 to Applied-AI job descriptions and leans on the one thing other candidates lack — your payments domain.
- **If you keep refining the plan instead of starting:** `fx-mcp-server` stays your only artifact in three months.

---

## 9. First concrete action

Start Week 1, Day 1: download the corpus and write `ingest.py`. Nothing about
this plan needs to be improved before you begin.

Optional accelerator: draft `eval/qa_set.jsonl` early (10 real payments
questions + the message/field each targets) so Week 2's most-skipped step is
already half-built.