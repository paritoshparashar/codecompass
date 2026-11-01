# Class for the issue being processed
__all__ = ["Issue", "IssueStatus", "IssueType"]

from enum import Enum, auto

from ..domain.candidate_package import Candidate
from .token_package.token import Token


class IssueStatus(Enum):
    OPEN = auto()
    IN_PROGRESS = auto()
    RESOLVED = auto()
    CLOSED = auto()


class IssueType(Enum):
    BUG = auto()
    FEATURE = auto()
    DOCUMENTATION = auto()
    PERFORMANCE = auto()
    TEST_GAP = auto()
    UNKNOWN = auto()


class Issue:
    def __init__(self, issue_id: int, description: str, title: str = ""):
        self.issue_id: int = issue_id
        self.title: str = title
        self.description: str = description
        self._tokens: list[Token] = []  # List of tokens extracted from the issue
        self.label: IssueType = IssueType.UNKNOWN
        self.status: IssueStatus = IssueStatus.OPEN
        self.localized_candidates: list[Candidate] = []  # List of localized candidates for the issue

    def __repr__(self):
        return f"Issue(issue_id={self.issue_id}, title={self.title})"

    def set_tokens(self, tokens: list[Token]):
        """Set the tokens for the issue."""
        self._tokens = tokens

    def get_tokens(self) -> list[Token]:
        """Get the tokens for the issue."""
        return self._tokens

    def get_localized_candidates(self) -> list[Candidate]:
        """Get the localized candidates for the issue."""
        return self.localized_candidates

    def add_localized_candidate(self, candidate: Candidate):
        """Add a localized candidate to the issue."""
        self.localized_candidates.append(candidate)

    def add_localized_candidates(self, candidates: list[Candidate]):
        """Add multiple localized candidates to the issue."""
        self.localized_candidates.extend(candidates)
