# Classes defining the request and response models for the repository initialization endpoint
__all__ = [
    "InitializeRepositoryRequest",
    "InitializeRepositoryResponse",
    "IssueLocalizationRequest",
    "IssueLocalizationResponse",
    "ResponseStatus",
]

from enum import Enum, auto

from pydantic.v1 import BaseModel

from ..domain.candidate_package.candidate_interface import Candidate


class ResponseStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()


# I/O Objects for the Repository Initialization Endpoint
class InitializeRepositoryRequest(BaseModel):
    git_url: str = "exampleURL.com"
    branch: str = "main"

class InitializeRepositoryResponse(BaseModel):
    status: ResponseStatus
    repository_id: str | None


# I/O Objects for the Issue Localization Endpoint
class IssueLocalizationRequest(BaseModel):
    repository_id: int
    issue: str

class IssueLocalizationResponse(BaseModel):
    status: ResponseStatus
    localized_candidates: list[Candidate] | None

    class Config:
        arbitrary_types_allowed = True  # Required in Pydantic v1 for Candidate objects
