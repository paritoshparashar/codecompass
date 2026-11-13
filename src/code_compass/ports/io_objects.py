from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


@dataclass
class InputRequest(ABC):
    set_by_user: bool = field(default=False, init=False)
    message: list[str] | None = None


@dataclass
class URLRequest(InputRequest):
    url: str | None = None
    branch: str  = "main"


@dataclass
class IssueRequest(InputRequest):
    file_path: Path | None = None


@dataclass
class NextActionRequest(InputRequest):

    class NextAction(Enum):
        NEW_ISSUE = "new_issue"
        NEW_REPOSITORY = "new_repository"
        EXIT = "exit"

    next_action: NextAction | None = None