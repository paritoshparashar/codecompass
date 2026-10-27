# Classes defining the request and response models for the repository initialization endpoint
__all__ = ["InitializeRepositoryRequest", "InitializeRepositoryResponse", "IssueLocalizationRequest", "IssueLocalizationResponse", "ResponseStatus"]

from enum import Enum, auto

from pydantic.v1 import BaseModel

from ..domain.repository_package.document import Document


class ResponseStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()


# I/O Objects for the Repository Initialization Endpoint
class InitializeRepositoryRequest(BaseModel):
    def __init__(self, git_url: str = "exampleURL.com", branch: str = "main"):
        self.git_url = git_url
        self.branch = branch


class InitializeRepositoryResponse(BaseModel):
    def __init__(self, status: ResponseStatus, repository_id: str | None):
        self.status = status
        self.repository_id = repository_id


# I/O Objects for the Issue Localization Endpoint
class IssueLocalizationRequest(BaseModel):
    def __init__(self, repository_id: str, issue: str):
        self.repository_id = repository_id
        self.issue = issue


class IssueLocalizationResponse(BaseModel):
    def __init__(self, status: ResponseStatus, localized_candidates: list[Document] | None):
        self.status = status
        self.localized_candidates = localized_candidates
