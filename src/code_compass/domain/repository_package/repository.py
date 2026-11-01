# Class for representing a repository
__all__ = ["Repository"]

from collections.abc import Sequence
from enum import Enum, auto
from pathlib import Path

from ..issue import Issue
from .document import Document


class ReadOnlySequence(Sequence):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)


class Repository:
    class State(Enum):
        NOT_INITIALIZED = auto()  # system is not initialized yet
        INITIALIZED = auto()  # system is ready to accept a new issue

    def __init__(
        self,
        id: int,
        name: str,
        url: str,
        path: Path,
        state: State = State.NOT_INITIALIZED,
    ):
        self._id: int = id
        self._name: str = name
        self._url: str = url
        self._path: Path = path
        self._documents: list[
            Document
        ] = []  # Sequence of Document objects associated with this repository
        self._documents_view = ReadOnlySequence(
            self._documents
        )  # Read-only view of the documents
        self._issues: list[Issue] = []  # List of issues associated with this repository
        self.state: Repository.State = state  # State of the repository

    # Immutable properties for the Repository class

    @property
    def id(self) -> int:
        return self._id

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
        return f"Repository(id={self.id}, name={self.name})"

    def get_issues(self) -> list[Issue]:
        """Get the list of issues associated with the repository."""
        return self._issues

    def get_issue(self, issue_id: int) -> Issue | None:
        """Get an issue by its ID."""
        for issue in self._issues:
            if issue.issue_id == issue_id:
                return issue
        return None

    def add_issue(self, issue: Issue) -> None:
        """Add an issue to the repository."""
        self._issues.append(issue)

    def remove_issue(self, issue: Issue) -> None:
        """Remove an issue from the repository."""
        self._issues.remove(issue)