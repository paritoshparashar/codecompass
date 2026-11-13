__all__ = ["CodeCompassPipeline"]

from typing import cast

from code_compass.application.classification_package.classification_service import (
    ClassificationService,
)
from code_compass.application.initialization_package.repostiory_initialization_service import (
    RepositoryInitializationService,
)

from ..application.localization_package.localization_service import LocalizationService
from ..application.service import Service
from ..domain.issue import Issue, IssueType
from ..domain.repository_package.repository import Repository
from ..domain.repository_package.repository_manager import RepositoryManager
from ..domain.systemStates import SystemState
from ..logger import Logger
from ..pipeline.io_module import (
    CreateIssueRequest,
    CreateIssueResponse,
    InitializeRepositoryRequest,
    InitializeRepositoryResponse,
    IssueClassificationRequest,
    IssueClassificationResponse,
    IssueLocalizationRequest,
    IssueLocalizationResponse,
    ResponseStatus,
)
from .service_creater import ServiceCreater, ServiceType


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
        #  store: "RunStore"
        self.services: dict[ServiceType, Service | None] = {
            ServiceType.INITIALIZATION: None,
            ServiceType.LOCALIZATION: None,
            ServiceType.CLASSIFICATION: None,
        }
        self.service_creater = ServiceCreater()
        self.start_services(self.service_creater)
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
        self.services[ServiceType.INITIALIZATION] = (
            creator.create_initialization_service()
        )
        self.services[ServiceType.LOCALIZATION] = creator.create_localization_service()
        self.services[ServiceType.CLASSIFICATION] = (
            creator.create_classification_service()
        )

    # def process(self, issue: Issue, config: Settings) -> RunReport:
    def create_and_initialize_repository(
        self, respoistoryRequest: InitializeRepositoryRequest
    ) -> InitializeRepositoryResponse:

        initialization_service: RepositoryInitializationService = cast(
            RepositoryInitializationService, self.services[ServiceType.INITIALIZATION]
        )
        Logger.log_start("Pipeline: Started")
        # Call create and initialize repository
        if initialization_service is None:
            raise ValueError("Initialization service is not set.")
        repository: Repository | None = initialization_service.initialize_repository(
            respoistoryRequest.git_url, respoistoryRequest.branch
        )
        if repository is None:
            return InitializeRepositoryResponse(status=ResponseStatus.FAILURE)
        repository.state = Repository.State.INITIALIZED
        self.repositoryManager.add_repository(repository)
        return InitializeRepositoryResponse(
            status=ResponseStatus.SUCCESS,
            repository_id=repository.id,
            repository_name=repository.name,
            issue_folder=repository.issue_folder,
        )

    def create_issue(
        self, create_issue_request: CreateIssueRequest
    ) -> CreateIssueResponse:
        repository = self.repositoryManager.get_repository(
            create_issue_request.repository_id
        )
        if repository is None:
            Logger.log(
                f"Repository with ID {create_issue_request.repository_id} not found : {Logger.red('Exiting with error')}"
            )
            return CreateIssueResponse(status=ResponseStatus.FAILURE)

        # Read the issue description from the file
        try:
            with open(create_issue_request.file_path, "r") as file:
                issue_description = file.read().strip()
        except OSError as e:
            Logger.log(
                f"Failed to read issue description from {create_issue_request.file_path}: {e} : {Logger.red('Exiting with error')}"
            )
            return CreateIssueResponse(status=ResponseStatus.FAILURE)
        # Create a new issue and add it to the repository
        new_issue_id = self.getNextIssueIdForRepository(
            create_issue_request.repository_id
        )
        issue = Issue(
            issue_id=new_issue_id,
            description=issue_description,
        )
        repository.add_issue(issue)
        return CreateIssueResponse(
            status=ResponseStatus.SUCCESS,
            issue_id=issue.get_id(),
        )

    def localize_issue(
        self, localization_request: IssueLocalizationRequest
    ) -> IssueLocalizationResponse:

        repository = self.repositoryManager.get_repository(
            localization_request.repository_id
        )
        if repository is None:
            return self.localization_failure(
                f"Repository with ID {localization_request.repository_id} not found : {Logger.red('Exiting with error')}"
            )
        if repository.state != Repository.State.INITIALIZED:
            return self.localization_failure(
                f"Issue Localization attempted before Repository Initialization : {Logger.red('Exiting with error')}"
            )

        issue = repository.get_issue(localization_request.issue_id)
        if issue is None:
            return self.localization_failure(
                f"Issue with ID {localization_request.issue_id} not found in Repository {localization_request.repository_id} : {Logger.red('Exiting with error')}"
            )

        # Call the localization service
        localization_service: LocalizationService = cast(
            LocalizationService, self.services[ServiceType.LOCALIZATION]
        )
        if localization_service is None:
            return self.localization_failure("Localization service is not set.")

        localized_candidates: list | None = localization_service.localize_issue(
            issue=issue,
            repository=repository,
        )
        if localized_candidates is None:
            return self.localization_failure(
                f"Localization service failed to localize the issue : {Logger.red('Exiting with error')}"
            )

        issue.add_localized_candidates(localized_candidates)

        # Update the repository state to LOCALIZED after successful localization
        repository.state = Repository.State.LOCALIZED

        return IssueLocalizationResponse(
            status=ResponseStatus.SUCCESS, localized_candidates=localized_candidates
        )

    def localization_failure(self, message: str) -> IssueLocalizationResponse:
        Logger.log(f"{message}")
        return IssueLocalizationResponse(status=ResponseStatus.FAILURE)

    def classify_issue(
        self, classification_request: IssueClassificationRequest
    ) -> IssueClassificationResponse:

        repository = self.repositoryManager.get_repository(
            classification_request.repository_id
        )
        if repository is None:
            return self.classification_failure(
                f"Repository with ID {classification_request.repository_id} not found : {Logger.red('Exiting with error')}"
            )

        issue = repository.get_issue(classification_request.issue_id)
        if issue is None:
            return self.classification_failure(
                f"Issue with ID {classification_request.issue_id} not found in Repository {classification_request.repository_id} : {Logger.red('Exiting with error')}"
            )

        classification_service: ClassificationService = cast(
            ClassificationService, self.services[ServiceType.CLASSIFICATION]
        )

        if classification_service is None:
            return self.classification_failure("Classification service is not set.")

        issueType: IssueType | None = classification_service.classify_issue(issue)
        if issueType is None:
            return self.classification_failure(
                f"Classification service failed to classify the issue : {Logger.red('Exiting with error')}"
            )

        # Update the repository state to CLASSIFIED and the issue label
        repository.state = Repository.State.CLASSIFIED
        issue.label = issueType

        return IssueClassificationResponse(
            status=ResponseStatus.SUCCESS,
            classification_result=issueType,
        )

    def classification_failure(self, message: str) -> IssueClassificationResponse:
        Logger.log(f"{message}")
        return IssueClassificationResponse(status=ResponseStatus.FAILURE)

    def getNextIssueIdForRepository(self, repository_id: int) -> int:
        repository = self.repositoryManager.get_repository(repository_id)
        if repository is None:
            raise RepositoryNotFoundError(
                f"Repository with ID {repository_id} not found."
            )
        # check the highest issue ID in the repository and return the next one
        if not repository.get_issues():
            return 1
        return max(issue.get_id() for issue in repository.get_issues()) + 1

    def get_issue_root_folder(self) -> str:
        return str(self.service_creater.get_issue_root_folder())

    def end(self):
        Logger.log_end("Pipeline Ended")
