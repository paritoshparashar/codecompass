# Pillar 3: Information Retrieval & Code Search

---

## 1. Robertson–Spärck Jones Okapi BM25

BM25 (Best Matching 25) is a ranking function used by search engines to score the relevance of a candidate document $D$ to a search query $Q = \{q_1, q_2, \dots, q_n\}$.

$$\text{Score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

Where:
- $f(q_i, D)$ is the raw term frequency of query token $q_i$ in document $D$.
- $|D|$ is the length of document $D$ (total token count).
- $\text{avgdl}$ is the average document length across the entire corpus.
- $k_1$ and $b$ are tuning hyperparameters.

---

## 2. Why BM25 Outperforms TF-IDF on Code Search

Traditional TF-IDF suffers from two major pathologies when applied to source code:

### 1. Linear Term Frequency Exploitation vs. $TF$ Saturation ($k_1$)
- **TF-IDF:** Uses linear or logarithmic term frequency. If a long source file contains 50 occurrences of the word `data`, TF-IDF gives it massive weight simply because of repetition.
- **BM25 Saturation:** The hyperparameter $k_1$ (typically $1.2 - 2.0$, default $1.5$) sets an **asymptote (ceiling)** on term frequency contribution.
  - The first few occurrences of a query term provide the largest score increase.
  - Repeating the word 50 times yields diminishing returns, approaching a maximum multiplier of $(k_1 + 1)$.
  - **Code Benefit:** Prevents large loop bodies or repetitive variable names from drowning out concise functions that actually implement the logic.

### 2. Document Length Bias vs. Length Normalization ($b$)
- **The Issue in Codebases:** A small 15-line helper function (`math_utils.py`) has very few total tokens, while an 800-line controller (`api_router.py`) has thousands of tokens.
- **Length Penalty ($b$):** The hyperparameter $b$ (between $0.0$ and $1.0$, default $0.75$) controls how aggressively long documents are penalized:
  - If $b = 1.0$: Fully scales by relative document length ($\frac{|D|}{\text{avgdl}}$).
  - If $b = 0.0$: Ignores document length entirely.
  - At $b = 0.75$: A short function matching 2 query terms gets a fair boost relative to a huge file that casually mentions the terms in comments.

---

## 3. Smoothed Non-Negative Inverse Document Frequency (IDF)

In our `BM25Scorer`, the Robertson–Spärck Jones formula is implemented as:

$$\text{IDF}(q_i) = \ln\left(1 + \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5}\right)$$

Where:
- $N$ is total documents in the corpus.
- $n(q_i)$ is the number of documents containing query term $q_i$.

### Why the `1 +` and `+ 0.5` Smoothing is Critical:
- If a query term appears in almost every document ($n(q_i) > N/2$), classic formulas yield a **negative IDF**, penalizing documents that contain the word!
- Adding `1 + (...)` inside the natural logarithm guarantees:
  $$\text{IDF}(q_i) \ge 0$$
  High-frequency stop words approach $0$, but never become negative penalties.

---

## 4. Code-Aware Tokenization & The Vocabulary Gap

### The Problem
Issue tickets are written in natural English (*"Export batch fails on invoice"*). Source code is written in compound syntax identifiers (`export_batch_records`, `InvoiceService`).

A standard NLP tokenizer splitting on whitespace treats `export_batch_records` as a single indivisible token, failing to match the user's query word `"export"`.

### The Solution: Multi-Level Sub-Token Extraction
Our `Tokenizer` implements a multi-step pipeline:
1. **Identifier Extraction:** Extracts valid programming identifiers and numbers via `[A-Za-z_][A-Za-z0-9_]*|[0-9]+`, cleanly stripping syntax punctuation (`(`, `)`, `:`, `.`).
2. **Sub-Token Decomposition:**
   - **snake_case:** `calculate_export_total` $\rightarrow$ `['calculate', 'export', 'total']`.
   - **camelCase:** `getUserAccount` $\rightarrow$ `['get', 'user', 'account']`.
   - **PascalCase:** `HTTPClient` $\rightarrow$ `['http', 'client']`.
3. **Compound Preservation:** Retains both the sub-tokens AND the full compound identifier (`calculate_export_total`), allowing exact matches and partial semantic matches.
4. **Frequency Retention:** Returns a `list[Token]` (preserving duplicates) rather than a `set`, ensuring accurate BM25 term frequency counting.

