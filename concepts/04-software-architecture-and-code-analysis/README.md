# Pillar 4: Software Architecture & Code Analysis

---

## 1. AST (Abstract Syntax Tree) vs. Regex for Code Parsing

When localizing an issue to a specific code entity (A5 in PROBLEM.md: File $\rightarrow$ Function $\rightarrow$ Line), how should the codebase be chunked into candidates?

### Why Regex Fails on Code Extraction
Using regular expressions like `r"def\s+(\w+)\s*\("` breaks down because:
1. **No Scope Awareness:** Matches `def` inside comments, multi-line strings, or docstrings.
2. **Missing Boundary Lines:** Regex finds where a function *starts*, but cannot determine where it *ends* (requires parsing indentation, nested blocks, and async scopes).
3. **Fragile to Formatting:** Fails on decorators, type annotations across multiple lines, and async function signatures.

### Why `ast.parse` is Architecturally Superior
Python's built-in `ast` module compiles Python code into a formal syntax tree:

```python
tree = ast.parse(content, filename=str(document.path))

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        start_line = node.lineno
        end_line = node.end_lineno  # Exact line range!
        function_name = node.name
```

**Benefits in CodeCompass:**
- **Exact Line Ranges:** `node.lineno` to `node.end_lineno` gives the exact lines for `FunctionCandidate`.
- **Fault-Tolerant:** Wrapped in a `try...except SyntaxError:` block, allowing the pipeline to analyze partially invalid repositories without crashing.
- **Pure Standard Library:** Zero heavy C++ bindings or external parser dependencies for v1.

---

## 2. Domain-Driven Design (DDD): Aggregate Roots & Read-Only Views

In Domain-Driven Design, a `Repository` is an **Entity** with mutable state that evolves over its lifecycle, but its identity attributes (`id`, `name`, `url`, `path`) must remain strictly immutable.

### The Invariant Protection Problem
If `repo.documents` is exposed as a raw Python `list`:
```python
repo.documents.append(bad_doc)  # Callers bypass validation!
```
Any outside service could mutate repository documents without the repository's knowledge.

### The "Stale Snapshot" Trap
Returning a new tuple snapshot (`return tuple(self._documents)`) prevents mutation, but creates a **stale reference**:
```python
cached_docs = repo.documents  # Snapshot at T1
repo.add_document(new_doc)    # Added at T2
# cached_docs does not reflect the update!
```

### The Solution: `ReadOnlySequence` View
We implemented a live read-only wrapper implementing `collections.abc.Sequence`:

```python
class ReadOnlySequence(Sequence):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)
```

1. **Always Live:** Inspects `self._data` directly. Never gets stale.
2. **Strictly Read-Only:** Attempting `repo.documents.append(doc)` raises `AttributeError`.
3. **High Performance ($O(1)$):** No memory copies or new tuple allocations.

---

## 3. The Strategy Pattern & Composition Root

### Strategy Pattern
In `code_compass.application.localization_package.localization_strategy`:
- `LocalizationStrategy` defines a Python `Protocol` specifying:
  `localize(candidates, issue, top_k) -> list[Candidate]`
- `BM25LocalizationStrategy` is one interchangeable implementation.
- In future milestones, dense vector embeddings or hybrid rerankers plug directly into `LocalizationService` without changing a single line of service logic (Open/Closed Principle).

### Composition Root (`ServiceCreater`)
The Composition Root is the centralized location where dependency graphs are assembled:
- The orchestrator (`CodeCompassPipeline`) does not instantiate low-level scorers directly.
- It delegates instantiation to `ServiceCreater`, which reads `LocalizationConfig` and wires `BM25Scorer` $\rightarrow$ `BM25LocalizationStrategy` $\rightarrow$ `LocalizationService`.

