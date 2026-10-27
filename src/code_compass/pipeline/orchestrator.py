__all__ = ["CodeCompassPipeline"]

from ..domain.issue import Issue
from ..domain.repository_package.repository import Repository
from ..domain.repository_package.repository_manager import RepositoryManager
from ..domain.systemStates import SystemState
from ..logger import Logger
from ..pipeline.io_module import (
    InitializeRepositoryRequest,
    InitializeRepositoryResponse,
    IssueLocalizationRequest,
    IssueLocalizationResponse,
    ResponseStatus,
)
from .service_creater import ServiceCreater


class RepositoryNotFoundError(Exception):
    """Raised when a requested repository is not registered."""


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
        #  ranker: HybridRanker,
        #  evluator: EvidenceEvaluator,
        #  guide: GuideGenerator,
        #  feedback: FeedbackController,
        #  store: "RunStore")
        self.start_services(ServiceCreater())
        self.state = SystemState.NOT_INITIALIZED
        self.repositoryManager = RepositoryManager()
        self.issue: Issue | None = None
        self.classifier = None
        self.ranker = None
        self.evaluator = None
        self.guide = None
        self.feedback = None
        self.store = None

    def start_services(self, creator: ServiceCreater):
        self.initialization_service = creator.create_initialization_service()
        self.localization_service = creator.create_localization_service()

    # def process(self, issue: Issue, config: Settings) -> RunReport:
    def create_and_initialize_repository(
        self, respoistoryRequest: InitializeRepositoryRequest
    ) -> InitializeRepositoryResponse:

        Logger.log_start("Pipeline: Started")
        # Call create and initialize repository

        repository: Repository | None = (
            self.initialization_service.initialize_repository(
                respoistoryRequest.git_url, respoistoryRequest.branch
            )
        )
        if repository is None:
            return InitializeRepositoryResponse(
                status=ResponseStatus.FAILURE,
                repository_id=None,
            )
        self.repositoryManager.add_repository(repository)
        self.state = SystemState.INITIALIZED
        return InitializeRepositoryResponse(
            status=ResponseStatus.SUCCESS,
            repository_id=str(repository.id),
        )

    def localize_issue(
        self, localization_request: IssueLocalizationRequest
    ) -> IssueLocalizationResponse:

        if self.state != SystemState.INITIALIZED:
            Logger.log(
                f"Issue Localization attempted before repository initialization : {Logger.red('Exiting with error')}"
            )
            return IssueLocalizationResponse(
                status=ResponseStatus.FAILURE,
                localized_candidates=None,
            )
        self.issue = Issue(
            issue_id=0,
            description=localization_request.issue,
        )

        # Call the localization service
        localized_candidates = self.localization_service.localize_issue(
            issue=self.issue,
            repository=self.repositoryManager.get_repository(
                localization_request.repository_id
            ),
        )
        if localized_candidates is None:
            return IssueLocalizationResponse(
                status=ResponseStatus.FAILURE,
                localized_candidates=None,
            )

        return IssueLocalizationResponse(
            status=ResponseStatus.SUCCESS, localized_candidates=localized_candidates
        )

    def end(self):
        Logger.log_end("Pipeline Ended")
