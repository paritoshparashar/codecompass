from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl

from src.application.initialization.initializeRepo import (
    RepositoryInitializationService
)
app = FastAPI()

# Classes defining the request and response models for the repository initialization endpoint
class InitializeRepositoryRequest(BaseModel):
    git_url: HttpUrl = "exampleurl.com"
    branch: str = "main"

class InitializeRepositoryResponse(BaseModel):
    status: str
    message: str
    repository_id: str

# Create the repo initialize service instance
repo_init_service = RepositoryInitializationService(repoPath=Path("path/to/repo"))

# Post Endpoint - To clone a repository from a given git URL and initialize it in the system
@app.post("/create_repository",
          response_model = InitializeRepositoryResponse,
          status_code=status.HTTP_201_CREATED,)
def create_repository(request: InitializeRepositoryRequest) -> InitializeRepositoryResponse:
    repository = repo_init_service.initialize_repository(request.git_url, request.branch)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository initialization failed.")
    
    # set the system state to READY after successful initialization / or how to do it think - per repo or per
    # for now, we can set it globally for the system
    # system_state = "READY"

    return InitializeRepositoryResponse(
        status="success",
        message="Repository initialized successfully.",
        repository_id=str(repository.repo_id)
    )
