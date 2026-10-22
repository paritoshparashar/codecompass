__all__ = ["CodeCompassPipeline"]

from pathlib import Path
from application.initialization import RepositoryInitializationService
from code_compass.logger import Logger
from code_compass.domain.repository.repository import Repository
from domain.systemStates import SystemState
from domain.repository.repository_manager import RepositoryManager
from pipeline.io_module import InitializeRepositoryRequest, InitializeRepositoryResponse

class CodeCompassPipeline:

    # 0 - The application starts - 
    #   0.1 - Populates the domain objects 
    #          [Creates the repo - docs, and whatever we can do before receiving the issue - 
    #           create the settings and configs for the application to run ]
    # 1 - Receive the issue
    # 2 - Populates the issue domain object 
    # 2 - Calls the LocalizationService with the issue object [the repo can be accessed globally]
    #   2.1 - Select the strategy from the config file [BM25, BM25+Embeddings, Embeddings]
    # 3 - Receives the LocalizationResult
    # 4 - Calls the ClassifierService
    # 4 - Receives the ClassificationResult

    def __init__(self):
             #  self, classifier: IssueClassifier,
                        #  ranker: HybridRanker,
                        #  evluator: EvidenceEvaluator,
                        #  guide: GuideGenerator,
                        #  feedback: FeedbackController,
                        #  store: "RunStore")
        self.initialization_service = RepositoryInitializationService(Path(__file__).parents[3] / "clonedRepository")
        self.state = SystemState.NOT_INITIALIZED
        self.repositoryManager = RepositoryManager()
        self.classifier = None
        self.ranker = None
        self.evaluator = None
        self.guide = None
        self.feedback = None
        self.store = None

    # def process(self, issue: Issue, config: Settings) -> RunReport:
    def startPipeline(self, initializeInput: InitializeRepositoryRequest) -> InitializeRepositoryResponse:
        Logger.log_start("Code Compass Started")
        # Call create and initialize repository
        try:
            repository: Repository = self.create_and_initialize_repository(initializeInput.git_url, initializeInput.branch)
            self.repositoryManager.add_repository(repository)
        except Exception as e:
            return InitializeRepositoryResponse(
                status="failure",
                message = str(e),
                repository_id = None
            )
        self.state = SystemState.INITIALIZED
        return InitializeRepositoryResponse(
                    status="success",
                    message="Repository initialized successfully.",
                    repository_id=str(repository.repo_id)
                )

    def create_and_initialize_repository(self, git_url: str, branch: str) -> Repository:
        try :
            repository = self.initialization_service.initialize_repository(git_url, branch)
        except Exception as e:
            Logger.log_end(f"Repository initialization failed: {e}")
            raise e
        # set the system state to READY after successful initialization / or how to do it think - per repo or per
        # for now, we can set it globally for the system
        # system_state = "READY"

        return repository

    def end(self):
        Logger.log_end("Code Compass Ended")

