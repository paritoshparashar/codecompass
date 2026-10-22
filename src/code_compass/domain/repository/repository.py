# Class for representing a repository
__all__ = ["Repository"]

from collections.abc import Sequence
from pathlib import Path
from code_compass.domain.repository.document import Document

class ReadOnlySequence(Sequence):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)

class Repository:
    def __init__(self, repo_id: int, name: str, url: str, path: Path):
        self._repo_id = repo_id
        self._name = name
        self._url = url
        self._path = path
        self._documents: list[Document] = []  # Sequence of Document objects associated with this repository
        self._documents_view = ReadOnlySequence(self._documents)  # Read-only view of the documents
    # Immutable properties for the Repository class

    @property
    def repo_id(self) -> int:
        return self._repo_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def path(self) -> Path:
        return self._path

    # Methods to manage documents associated with the repository

    @property
    def documents(self) -> Sequence[Document]:
        return self._documents_view

    def add_document(self, document: Document) -> None:
        self._documents.append(document)

    def remove_document(self, document: Document) -> None:
        self._documents.remove(document)

    def __repr__(self):
        return f"Repository(repo_id={self.repo_id}, name={self.name})"