# Classes defining the request and response models for the repository initialization endpoint
__all__ = ["InitializeRepositoryRequest", "InitializeRepositoryResponse"]

from pydantic.v1 import BaseModel

class InitializeRepositoryRequest(BaseModel):
    git_url: str = "exampleurl.com"
    branch: str = "main"

class InitializeRepositoryResponse(BaseModel):
    status: str
    message: str
    repository_id: str | None