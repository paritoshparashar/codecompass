# Pillar 2: Python Internals, Metaclasses & Modern Typing

---

## 1. Pydantic `BaseModel` Metaclasses vs. Standard Python Classes

### The Difference in Object Construction

In standard Python:
```python
class StandardRequest:
    def __init__(self, git_url: str, branch: str):
        self.git_url = git_url
        self.branch = branch
```
When `StandardRequest("url", "main")` runs, Python creates an empty instance dict (`self.__dict__`) and runs your `__init__` code to assign attributes dynamically.

In Pydantic:
```python
from pydantic.v1 import BaseModel

class InitializeRepositoryRequest(BaseModel):
    git_url: str = "exampleURL.com"
    branch: str = "main"
```

### Why Pydantic Metaclasses Forbid Custom `__init__` Dynamic Assignments

Pydantic classes are created by a **Metaclass** (`ModelMetaclass`). When the class definition is parsed at import time:
1. The metaclass inspects the class annotations (`git_url: str`, `branch: str`).
2. It builds internal schemas, type validators, default values, and serialization handlers.
3. It overrides `__setattr__` on instances.

If you bypass class annotations and define a custom `__init__`:
```python
# BROKEN PATTERN:
class BrokenRequest(BaseModel):
    def __init__(self, git_url: str):
        self.git_url = git_url  # <-- Pydantic's __setattr__ intercepts this!
```
Because `git_url` was never declared on the class body, Pydantic's internal model fields dictionary is empty. Calling `self.git_url = ...` raises:
```text
ValueError: "BrokenRequest" object has no field "git_url"
```

**Rule:** Always declare fields on the class body with type annotations. Let Pydantic's auto-generated `__init__` perform validation.

---

## 2. Dataclass Mechanics: `frozen=True` & `slots=True`

In CodeCompass, tokens are defined as:
```python
@dataclass(frozen=True, slots=True)
class Token:
    text: str
    normalized: str
    kind: TokenKind
```

### How `frozen=True` Works Under the Hood
When you pass `frozen=True`, Python automatically generates a custom `__setattr__` method:
```python
def __setattr__(self, name, value):
    raise FrozenInstanceError(f"cannot assign to field {name!r}")
```
- If you write a manual `__init__` that does `self.text = text`, Python calls `self.__setattr__` and crashes with `FrozenInstanceError`.
- Dataclass auto-generated initializers bypass this by calling `object.__setattr__(self, name, value)`.

### Why `slots=True` Matters for Performance
Normally, Python objects store their attributes in an open dictionary (`self.__dict__`). 
- A single Python dictionary adds significant memory overhead (150+ bytes per instance).
- For a large codebase with 100,000 code tokens, this consumes tens of megabytes of unnecessary RAM.
- `slots=True` tells Python: *"Do not create `__dict__`. Allocate a fixed, tiny array in C for only these attributes."*
- Result: **~60% memory reduction** and faster attribute access.

---

## 3. Python Import Machinery & Packaging (PEP 518 / PEP 621)

### `__name__` vs. `__package__` and Relative Imports
Why did `python src/code_compass/run.py` fail with `attempted relative import with no known parent package`?
- When a file is executed directly with `python path/to/file.py`, Python sets `__name__ = "__main__"` and `__package__ = None`.
- The moment Python hits `from . import pipeline`, it has no reference to what `.` is relative to.
- Running with `-m`: `PYTHONPATH=src python -m code_compass.run` sets `__package__ = "code_compass"`, resolving relative imports.

### The Role of `pyproject.toml` and Editable Installs (`pip install -e .`)
- **`[build-system]`**: Declares the build backend (e.g. `setuptools.build_meta`) per PEP 518.
- **Editable mode (`-e`)**: Pip creates an egg-link / `.pth` pointer directly to your `/src` folder inside `.venv/site-packages`. 
- **`[project.scripts]`**: Exposes CLI entry points:
  ```toml
  [project.scripts]
  codecompass = "code_compass.run:main"
  ```
  Generates a standalone binary in `.venv/bin/codecompass` that can be run from anywhere in the terminal.

