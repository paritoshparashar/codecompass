# Classes defining the request and response models for the repository initialization endpoint
__all__ = [
    "InitializeRepositoryRequest",
    "InitializeRepositoryResponse",
    "IssueClassificationRequest",
    "IssueClassificationResponse",
    "IssueLocalizationRequest",
    "IssueLocalizationResponse",
    "ResponseStatus",
]

from enum import Enum, auto
from pathlib import Path

from pydantic.v1 import BaseModel

from ..domain.candidate_package.candidate_interface import Candidate
from ..domain.issue import Issue, IssueType


class ResponseStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()


# I/O Objects for the Repository Initialization Endpoint
class InitializeRepositoryRequest(BaseModel):
    git_url: str = "exampleURL.com"
    branch: str = "main"


class InitializeRepositoryResponse(BaseModel):
    status: ResponseStatus
    repository_id: int = 0
    repository_name: str = ""
    issue_folder: Path = Path("")

# I/O Objects for the Issue Creation Endpoint
class CreateIssueRequest(BaseModel):
    repository_id: int
    file_path: Path

class CreateIssueResponse(BaseModel):
    status: ResponseStatus
    issue_id: int = 0

# I/O Objects for the Issue Localization Endpoint
class IssueLocalizationRequest(BaseModel):
    repository_id: int
    issue_id: int


class IssueLocalizationResponse(BaseModel):
    status: ResponseStatus
    localized_candidates: list[Candidate] = []

    class Config:
        arbitrary_types_allowed = True  # Required in Pydantic v1 for Candidate objects


# I/O Objects for the Issue Classification Endpoint
# Expects the Issue object already exists inside the Repository
class IssueClassificationRequest(BaseModel):
    issue_id: int
    repository_id: int


class IssueClassificationResponse(BaseModel):
    status: ResponseStatus
    classification_result: IssueType = IssueType.ABSTENTION
