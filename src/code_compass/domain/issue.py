# Class for the issue being processed

from enum import Enum, auto

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


class Issue:
    def __init__(self, issue_id: int, description: str, title: str = ""):
        self.issue_id = issue_id
        self.title = title
        self.description = description
        self.issueTokens: list[Token] = []  # List of tokens extracted from the issue
        self.label: IssueType = None  # Label can be set later
        self.status: IssueStatus = None  # Status can be set later

    def __repr__(self):
        return f"Issue(issue_id={self.issue_id}, title={self.title})"
