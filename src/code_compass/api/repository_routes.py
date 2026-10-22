from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
from pipeline.io_module import InitializeRepositoryRequest, InitializeRepositoryResponse
import pipeline
from code_compass.domain.repository.repository import Repository
from application.initialization.initializeRepo import (
    RepositoryInitializationService
)
app = FastAPI()

# Post Endpoint - To clone a repository from a given git URL and initialize it in the system
@app.post("/create_repository",
          response_model = InitializeRepositoryResponse,
          status_code=status.HTTP_201_CREATED,)
def create_repository(request: InitializeRepositoryRequest) -> InitializeRepositoryResponse:
    orchestrator = pipeline.CodeCompassPipeline()
    response: InitializeRepositoryResponse = orchestrator.startPipeline(request)
    if response.repository_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
    
    return response
    # set the system state to READY after successful initialization / or how to do it think - per repo or per
    # for now, we can set it globally for the system
    # system_state = "READY"
