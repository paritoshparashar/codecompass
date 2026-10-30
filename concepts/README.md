# CodeCompass — Concepts to Master for Technical Interviews

This directory serves as the knowledge repository for the engineering decisions, algorithms, and Python internals implemented throughout the CodeCompass project. 

Each guide is designed to help you explain and defend the architecture in senior AI and software engineering interviews.

---

## The Four Engineering Pillars

### 1. [Testing & Isolation](./01-testing-and-isolation/README.md)
- **The Test Pyramid in AI Engineering**: Pure math unit tests $\rightarrow$ Domain component tests $\rightarrow$ End-to-end integration pipelines.
- **Mocking External I/O**: Why `@patch.object` is used to mock external Git calls, file I/O, and networks.
- **Dynamic Side-Effects in Mocks**: Simulating realistic filesystem behavior with temporary sandboxes.

### 2. [Python Internals & Modern Typing](./02-python-internals-and-typing/README.md)
- **Pydantic Model Metaclasses vs. Standard Classes**: Why class annotations are mandatory and custom `__init__` breaks metaclass field registration.
- **Dataclass Mechanics (`frozen=True` & `slots=True`)**: How `__setattr__` mutation works under the hood and why custom `__init__` clashes with frozen models.
- **Python Import Machinery & Packaging**: Absolute vs. relative imports, `__name__` vs. `__package__`, and editable installations (`pip install -e .` with PEP 518/621).

### 3. [Information Retrieval & Code Search](./03-information-retrieval-and-nlp/README.md)
- **Robertson–Spärck Jones Okapi BM25**: Mathematical derivation, Term Frequency ($TF$) saturation ($k_1$), document length penalization ($b$), and non-negative smoothed IDF.
- **Why BM25 Outperforms TF-IDF on Code**: Combatting verbosity bias and keyword repetition in codebases.
- **Code-Aware Tokenization**: Bridging the "vocabulary gap", sub-token splitting (camelCase, PascalCase, snake_case), and preserving term frequencies.

### 4. [Software Architecture & Code Analysis](./04-software-architecture-and-code-analysis/README.md)
- **AST (Abstract Syntax Tree) vs. Regex for Code Parsing**: Why Python's `ast.parse` is essential for hierarchical localization (file $\rightarrow$ function line ranges).
- **Domain-Driven Design (DDD) Aggregates & Read-Only Views**: Protecting invariants with `ReadOnlySequence` without suffering from stale snapshots.
- **The Strategy Pattern & Composition Root**: Decoupling retrieval algorithms from pipeline orchestration via interfaces/protocols.

