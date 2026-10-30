# CodeCompass — PROBLEM.md

*The problem definition document. Everything else in the repo is justified by (or judged against) this file. Written 2026-10-07. Revisited weekly; frozen after Week 2 except by explicit decision.*

---

## 1. The problem, stripped to its core

A person has a **symptom described in human vocabulary** ("the export is slow", "the webhook 500s on renewal") and needs a **mechanism located in code vocabulary** (`export_batch()` in `reports/export.py`, the N+1 query at line 214).

The entire system exists to bridge this **vocabulary gap**. Every component is one strategy for the bridge:

- Embeddings assume symptom words and code words share semantic space. (Often false: the ticket says "renewal"; the code calls it `invoice.paid`.)
- BM25 assumes the ticket literally names files/functions. (True for developer-written tickets; false for user-written ones.)
- The dependency graph assumes the mechanism is reachable from structurally central things. (True — bugs live where traffic flows.)
- Execution evidence bypasses the vocabulary gap entirely: a traceback does not care what the ticket called the problem.

**Design invariant:** *execution is vocabulary-independent.* This is why "show, don't tell" is architecturally principled, not a UX preference.

---

## 2. Formal task definition

**Inputs:** issue text `T`, repository snapshot `R`, optionally available runtime artifacts (stack traces, logs, CI output).

**Outputs:**
1. **Localization**: ranked candidate locations — file → function → line.
2. **Issue-type distribution**: probabilistic classification with abstention, e.g. `{Bug: 0.65, Feature: 0.25, Test-gap: 0.10}`.
3. **Evidence bundle**: issue-type-specific observations collected at the candidate locations.
4. **Evaluation/diagnosis**: what the observations imply — grounded in the evidence, with citations to real repo entities only.
5. **Action plan / next steps**, and where applicable, a **validation** step (e.g., the repro test re-run after a fix).

**Ground truth (for evaluation):** the files/functions actually changed in the commit/PR that resolved the issue, mined from closed-issue history via closing-keyword links.

**Pipeline (aligned architecture):**

```
Issue + Repository + available artifacts
        │
        ├─→ Classification ("what kind?") ──(probabilistic + abstention)
        └─→ Localization ("where to look?") ──(candidate locations, not evidence)
                        │
                        ▼
        Issue-specific evidence collection (at candidate locations;
        strategy selected by classification hypothesis)
                        │
                        ▼
        Evidence evaluation ("what do the observations imply?")
                        │
                        ▼
        Diagnosis / action plan → validation
                        │
        └── feedback: evaluation/validation may trigger re-classification
            or re-localization (feedback loop, not a cycle)
```

Classification and localization run **in parallel**; neither is upstream of the other. (Extension, not v1: classification confidence may modulate localization width — wider retrieval on low-confidence tickets.)

---

## 3. Two regimes of real tickets

| | Regime A — symptom-level | Regime B — mechanism-adjacent |
|---|---|---|
| Written by | users / PMs | developers |
| Content | vague, sometimes wrong about what is happening | already suspects where/what |
| Localization difficulty | hard — mechanism must be inferred | near-trivial |
| Value of CodeCompass | orientation + evidence | evidence + next steps |
| v1 handling | abstention path ("underspecified — here is what I found + N clarifying questions") | full pipeline |

**Decision:** v1 targets Regime B; Regime A gets the abstention path, not a best-effort guess. (Rationale: wrong-but-confident is the catastrophic failure class — see §6.)

**Empirical validation required:** classify 30–50 real issues per benchmark repo by hand; record regime, type, and *which evidence would have helped*. [FILL: regime counts after Week 2 task]

---

## 4. Issue-type epistemics and evidence strategies

The five-way taxonomy is a hypothesis, validated against the §3 sample. The derivation per type: what is epistemically unknown → what closes the gap for a human expert → why prose fails → what evidence artifact embodies the philosophy.

**Bug — philosophy: experimental science.** Unknown: the mechanism; known: an oracle (it *is* broken). Expert method = hypothesis → experiment → delta-minimize. A reproduction test *is* the experiment. Prose fails: it reports a conclusion about an experiment the reader never saw. **Evidence: failing run + trace-diff against a passing reference execution.** Note: a bug is a *divergence*; divergence requires two observations — this is why bug evidence is fundamentally a diff. Success-rate calibration from literature: expect roughly a third of bug tickets to yield genuine repros (Issue2Test ≈ 33% on SWT-bench-lite) — that is a *success*, report honestly.

**Missing feature — philosophy: analogy, not experiment.** No oracle — nothing is broken; there is no failing run to observe. Expert method = structural analogy: "this codebase already does email verification; map it onto this request." Grounded in case-based reasoning and structure-mapping theory (humans map relational structure, not surface features — hence AST/graph similarity over token overlap). Prose fails: a written spec describes intent; the analog embodies the codebase's own conventions. **Evidence: nearest analog + scaffold (wired into the real router/module).** *The evidence for a bug is a divergence; the evidence for a feature is an analogy.* This is the philosophical justification for typed pipelines and it goes in the README.

**Missing test coverage — philosophy: falsification.** Unknown: unknown-unknowns. A coverage percentage measures what was executed (a statement about the past); it says nothing about whether tests can detect being wrong. Each mutant is a constructed counter-world; a surviving mutant is a **constructive proof of a blind spot**. Grounded in mutation-testing theory and validated at scale (Google: survivors surfaced as concrete diffs in code review; ~69% of studied historical bugs had a coupled mutant). Prose fails: "coverage is 72%" is undirected; a surviving mutant is a specific, actionable counterexample. **Evidence: surviving mutants, risk-ranked by graph centrality.**

**Missing documentation — philosophy: observation over declaration.** Documentation declares authorial intent; usage shows actual behavior. Generated docstrings are declarations — hypotheses that may not match reality (hence "subtly wrong"). **Evidence: mined real call sites + input/output pairs observed from test-suite execution.** Weakest of the five philosophically ("examples beat prose" is more folklore than measured result) → build last / stretch.

**Performance — philosophy: measurement over introspection.** Slowness is not incorrectness — no correctness oracle, only a budget. Vague tickets ("export is slow") still need localization first to pick *which path to profile*. **Evidence: observed execution under workload, compared against a baseline** (flame graph / differential profile). CPU vs I/O caveat: "slow" tickets are often I/O-bound, where plain flame graphs mislead — note it, don't solve it in v1.

**Unifying pattern (research hypothesis H5, NOT an established law):** issue resolution *often* involves generating observations and evaluating them against an issue-specific reference (bug → passing behavior; feature → requirements/analog; test-gap → original program; docs → declared behavior; perf → baseline). Counterexamples exist (a raw stack trace is already evidence). Do not claim universality anywhere public without a targeted literature review.

---

## 5. Decision inventory (capability sweep results)

Verdicts: **AI-anchor** = real training + evaluation (the ML story); **AI-tooling** = pretrained models, no training; **AI-light** = learned similarity, minor; **Hybrid**; **Engineering**.

### Phase A — shared spine (type-agnostic)

| ID | Decision | Technique (M1/no-budget fit) | Verdict |
|---|---|---|---|
| A1 | Structural centrality at index time | PageRank over call graph (`networkx`) | Engineering |
| A2 | **Issue-type classification + answerability/abstention** | Fine-tune MiniLM/DeBERTa-small on GitHub-labeled issues; temperature-scaled probabilities + threshold → abstain | **AI-anchor 1** (tests H4) |
| A3 | Retrieval: ~20 of ~10k chunks | BM25 (`bm25s`) + local code embedder (`sentence-transformers` on MPS), RRF with k=10–20 | AI-tooling |
| A4 | **Reranking to top-k** | CrossEncoder (MiniLM, ~22M params) + MNRL fine-tune on mined (issue → changed files) pairs | **AI-anchor 2** (tests H2/H3) |
| A5 | File → function → line narrowing | Engineering scaffold (graph expansion: file → functions → call sites) + LLM-assisted function ranking | Hybrid (LLM-on-8B is the weak link — flag) |

### Phase B — typed evidence strategies

| ID | Decision | Technique | Verdict |
|---|---|---|---|
| B1 | Bug: repro validity *and faithfulness* | Validity = sandbox execution (mechanical). Faithfulness (reproduces the *reported symptom*, not any failure) = LLM-judge **treated skeptically** | Engineering + weak-AI slot — **research risk**, feeds H5 |
| B2 | Bug: reference-execution selection | Embed failing frames/code; nearest passing test via similarity | AI-light |
| B3 | Feature: nearest analog | A3/A4 retrieval + graph-position feature (analog occupies similar structural role) | AI, reuses spine (tests H3) |
| B4 | Feature: scaffold soundness | AST parse, import resolution, route-registration checks | Engineering |
| B5 | Coverage: arid-mutant filtering | Heuristic filters (uncalled paths, equivalent-class patterns) | Engineering |
| B6 | Coverage: survivor ranking | PageRank centrality + reachability count | Engineering v1; learned = stretch ablation |
| B7 | Docs: representative call sites | Frequency + centrality ranking, outlier trimming | Engineering |
| B8 | Perf: what to profile | Uses spine; `py-spy` in sandbox on localized entry point | Engineering |

### Phase C — guide, feedback, meta

| ID | Decision | Technique | Verdict |
|---|---|---|---|
| C1 | Guide generation | LLM constrained to cite only entities present in the evidence bundle (graph-grounding as hallucination defense) | AI (LLM) + engineering guardrails |
| C2 | Backend selection per guide call | **Thompson Sampling over {Ollama-local, Groq-free-tier}** | **AI-anchor 3** (tests H1) |
| C3 | Staleness / retrain trigger | Threshold on mined-pair accumulation + rolling eval of Recall@k | Engineering |

---

## 6. Failure taxonomy

| Class | Example | Defense | Severity |
|---|---|---|---|
| Retrieval miss | Right file never in candidates | Better retrieval/graph signal (A3/A4/A5) | Fatal — nothing downstream recovers |
| Right file, wrong function | Points to `export.py`, wrong method | A5 hierarchical narrowing | High |
| Valid-looking evidence, wrong diagnosis | Repro test fails for env reasons | B1 faithfulness check (weak — see risk) | High |
| Right evidence, hallucinated guide | Guide invents a nonexistent function | C1 grounding to evidence bundle | Medium |
| **Wrong but confident** | Bad localization presented as certain | A2 abstention + calibration | **Catastrophic** — one costs more trust than ten correct saves |
| Pipeline can't run | Repo doesn't install; flaky tests | Engineering, not AI | Fatal for demo |

Two consequences:
1. The catastrophic class is *wrong-but-confident* → the product metric is **precision at rank 1 + abstention behavior**, while the research metric is **Recall@k / MRR**. Measure both; the divergence is a talking point, not an inconsistency.
2. Not every row is an AI problem — scope decisions are defended via this table.

---

## 7. Evaluation design

**Benchmark repos:** `pallets/flask`, `pydantic/pydantic`, `encode/httpx` (swap/add django/sympy if mining volume is thin — target: a few hundred issue→files pairs per repo).

**Split:** chronological time-split; newest ~20% held out. Never shuffle (leak prevention). State this in the README explicitly.

**Metrics:**
- Research: Recall@k (file and function level), MRR.
- Product: top-1 precision, abstention rate, and a 5-person human study (2 tasks each, CodeCompass vs. RAG-chat, measure time-to-first-useful-edit and "could you start fixing this? yes/no").

**Baselines:**
1. BM25 only
2. Dense-only
3. BM25 + dense RRF (no graph, no reranker)
4. Vanilla RAG-chat answer (the show-don't-tell strawman; must lose the demo)

**Ablations (each = one README row = one pre-answered interview question):** graph signal on/off; reranker on/off; fine-tuning on/off (the "gets better" curve); RRF k sweep (10–20 vs. 60).

---

## 8. Hypotheses (testable, not assumptions)

| ID | Hypothesis | Tested by | Arbiter |
|---|---|---|---|
| H1 | Cost/quality-aware LLM routing (bandit) beats always-cheapest and always-best | C2 vs. fixed-backend arms | Judge scores + cost log |
| H2 | Shared localization spine works as well as issue-specific localization | Per-type metrics on the spine vs. typed baselines | Recall@k per type |
| H3 | Repo-specific fine-tuning of the reranker improves localization over time | A4 on/off, curve over mined time-slices | Recall@5/MRR trend |
| H4 | Confidence-aware classification degrades more gracefully than hard routing | A2 calibrated vs. argmax, downstream evidence quality under error injection | Calibration (ECE) + end-task metric under mislabeling |
| H5 | Reference-based evidence framing improves diagnosis quality over generic agentic exploration | Bug pipeline (reference diff) vs. generic-agent condition on same tickets | Human study + faithfulness audit |

---

## 9. Success ladder (evaluate against this in December)

**Minimum credible:**
- Localization Recall@5 on mined issues clearly beats baselines 1–3 (define "clearly": ≥10 points), on ≥100 held-out issues.
- One evidence pipeline end-to-end on real mined bug tickets with honest success rates (~⅓ repro is a success).
- One-command reproducible eval harness.

**Good (target):**
- A4 fine-tuning shows measurable lift on time-split; the H3 "gets better" curve exists.
- Two evidence pipelines (bug + test-coverage).
- 5-person human study completed.

**Excellent (stretch, do not plan around):**
- Positive graph-signal ablation (weakest literature precedent → most original claim if positive).
- Feature analog-retrieval pipeline (B3).
- C2 bandit integrated and converging.

---

## 10. Constraints

- **Hardware:** M1 MacBook Pro only; no paid cloud. Consequence: all models small/local (MPS backend); Ollama for LLM (8B-class quantized); emergency GPU = free Colab T4 / Kaggle P100 (~30 h/wk). This constraint *strengthens* the product story (self-hosted, auditable, cost-controlled) — frame as a design decision.
- **Budget:** ~zero. Embeddings local; Groq free tier only.
- **Time:** full-time from 2026-10-07 to end of December (~12 weeks), hard financial deadline.
- **Team:** one person. Every component must justify itself against §6.

---

## 11. Timeline (re-anchored 2026-10-07)

- **Week 1 (Oct 7–13):** mining pass (PyDriller) on the three repos — validate pair volume; 30–50-issue manual sample (regime, type, would-have-helped evidence). *Deliverable: [FILL] pair counts, [FILL] regime distribution. If volume thin → swap repos now, not in November.*
- **Weeks 2–4:** tree-sitter parser + call graph; AST chunker; A3 ranker; eval harness v1 with baselines 1–3. *Deliverable: first Recall@k numbers.*
- **Weeks 5–9:** A5 hierarchical localization; sandbox v1 + bug pipeline (B1/B2); A2 classifier; A4 fine-tuning on time-split; **applications start ~week 7–8** (README skeleton + first numbers). *Deliverable: H3 curve; first demo.*
- **Weeks 10–12:** test-coverage pipeline (B5/B6); human study; README + results writeup; C2 bandit only if the rest is solid.

**Non-negotiable:** ~15% of time from mid-October onward goes to applications, framed as "project in progress; first results available."

---

## 12. Risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| B1 faithfulness judge unreliable | High | Scope honestly: report "reproduces any failure"; list symptom-faithfulness under future work (paper-style retreat, pre-planned) |
| Mining volume too thin on chosen repos | Medium | Swap in django/sympy (SWE-bench families — keeps comparability) |
| 8B local LLM too weak for A5/C1 | Medium | Route those calls to Groq free tier; keep local for cheap captions; measure the gap (it feeds H1) |
| Docker-on-M1 friction (I/O-heavy mutation/test runs) | Medium | Raise Docker VM resources; scope mutation runs to single modules |
| Scope creep into Regime A / extra evidence pipelines | High | §3 and §9 are the fence; anything outside requires explicitly revising this file |
| Applications deferred until "ready" | High | §11 non-negotiable; deadline risk is personal, not technical |

---

## 13. Open slots (fill by end of Week 2)

- [FILL] Mined pair counts per repo (from Week 1 mining pass).
- [FILL] Regime distribution + type distribution from the 30–50-issue manual sample; taxonomy adjustments implied.
- [FILL] Final thresholds on the success ladder (§9) once baseline numbers exist.
- [FILL] Targeted literature review confirming/refuting novelty of the reference-based framing (H5) before any public claim.
