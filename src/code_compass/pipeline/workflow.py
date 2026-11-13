# application/code_compass_application.py

from pathlib import Path

from code_compass.logger import Logger
from code_compass.pipeline.io_module import (
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
from code_compass.pipeline.orchestrator import CodeCompassPipeline
from code_compass.ports.input_port import InputPort
from code_compass.ports.io_objects import (
    InputRequest,
    IssueRequest,
    NextActionRequest,
    URLRequest,
)


class CodeCompassWorkflow:
    def __init__(
        self,
        pipeline: CodeCompassPipeline,
        inputPort: InputPort,  # can be any adapter that implements the InputPort interface
    ):
        self.pipeline = pipeline
        self.inputPort = inputPort
        self.current_repo_issue_folder: Path = Path("")  # Initialize with an empty Path
        self.current_issue_id: int = 0  # Initialize with a default value
        self.current_repository_id: int = 0  # Initialize with a default value

    def run(self):
        # STEP 1: Repository Initialization
        repository_initialization_response = self.repostiroy_initialization()
        if (
            repository_initialization_response.status != ResponseStatus.SUCCESS
            or repository_initialization_response.repository_id is None
        ):
            return self.exit_workflow()

        self.current_repository_id: int = (
            repository_initialization_response.repository_id
        )
        self.current_repo_issue_folder: Path = (
            repository_initialization_response.issue_folder
        )

        # STEP 2: Issue Creation
        create_issue_response = self.createIssue()
        if create_issue_response.status != ResponseStatus.SUCCESS:
            return self.process_next_action()

        self.current_issue_id: int = create_issue_response.issue_id

        # STEP 3: Issue Localization and Classification
        self.process_issue()

        self.exit_workflow()

    def process_next_action(self):
        input_request = NextActionRequest(
            next_action=None,
            message=[
                "What would you like to do next?",
                "1. Create a new issue",
                "2. Analyze a new repository",
                "3. Exit",
            ],
        )
        input_response = self.inputPort.get_input(input_request)
        if input_response.next_action is None:
            Logger.log("No action selected. Exiting.")
            return self.exit_workflow()

        action = input_response.next_action
        match action:
            case NextActionRequest.NextAction.NEW_ISSUE:
                self.createIssue()
            case NextActionRequest.NextAction.NEW_REPOSITORY:
                self.run()
            case NextActionRequest.NextAction.EXIT:
                self.pipeline.end()

    def process_issue(self):

        # STEP 3.1: Issue localization
        issue_localization_response = self.issue_localization()
        if issue_localization_response.status != ResponseStatus.SUCCESS:
            self.process_next_action()

        # STEP 3.2: Issue Classification
        issue_classification_response = self.issue_classification()
        if issue_classification_response.status != ResponseStatus.SUCCESS:
            self.process_next_action()

        issue_type = issue_classification_response.classification_result
        Logger.log(f"Issue type: {issue_type}")

        # Call Evidence Collection Service (when implemented)
        self.evidence_collection(self.current_issue_id, self.current_repository_id)

    def evidence_collection(self, issue_id: int, repository_id: int):
        # Placeholder for evidence collection logic
        Logger.log(
            f"Evidence collection for Issue ID {issue_id} in Repository ID {repository_id} is not yet implemented."
        )
        self.exit_workflow()

    def repostiroy_initialization(self) -> InitializeRepositoryResponse:
        input_request = URLRequest(
            url=None,
            message=[
                "Please enter the URL of the repository to analyze: ",
                "Please enter the branch to analyze (default is 'main'): ",
            ],
        )
        input_response = self.inputPort.get_input(input_request)
        github_url: str | None = input_response.url
        if github_url is None:
            Logger.log("No URL provided. Exiting.")
            return InitializeRepositoryResponse(status=ResponseStatus.FAILURE)
        branch: str = input_response.branch

        request = InitializeRepositoryRequest(git_url=github_url, branch=branch)
        response: InitializeRepositoryResponse = (
            self.pipeline.create_and_initialize_repository(request)
        )
        return response

    def createIssue(
        self,
    ) -> CreateIssueResponse:
        issueFilePath = self.current_repo_issue_folder / "new_issue_description.txt"
        issueFilePath.touch(exist_ok=True)
        Logger.log(
            f"\nA 'new_issue_description.txt' file has been created at {issueFilePath.parent}\n"
        )
        issue_request = IssueRequest(
            file_path=issueFilePath,
            message=[
                f"Please enter the issue description in the {issueFilePath.name} file, save it, and close the file when done."
            ],
        )
        input_response = self.inputPort.get_input(issue_request)
        if not input_response.set_by_user:
            return self.cleanup_issue_creation(issueFilePath)

        create_issue_request = CreateIssueRequest(
            repository_id=self.current_repository_id,
            file_path=issueFilePath,
        )
        create_issue_response = self.pipeline.create_issue(create_issue_request)
        issue_id = create_issue_response.issue_id
        # Rename the issue description file to include the issue ID if the issue was created successfully
        if create_issue_response.status == ResponseStatus.SUCCESS:
            new_issue_file_path = (
                self.current_repo_issue_folder / f"issue_{issue_id}.txt"
            )
            issueFilePath.rename(new_issue_file_path)
            Logger.log("Issue description file renamed")
            return create_issue_response
        else:
            return self.cleanup_issue_creation(issueFilePath)

    def cleanup_issue_creation(self, issueFilePath: Path) -> CreateIssueResponse:
        if issueFilePath.exists():
            issueFilePath.unlink()
            Logger.log(f"Issue description file {issueFilePath} deleted.")
        return CreateIssueResponse(status=ResponseStatus.FAILURE)

    def issue_localization(self) -> IssueLocalizationResponse:

        issue_localization_request = IssueLocalizationRequest(
            repository_id=self.current_repository_id, issue_id=self.current_issue_id
        )
        issue_localization_response: IssueLocalizationResponse = (
            self.pipeline.localize_issue(issue_localization_request)
        )
        return issue_localization_response

    def issue_classification(self) -> IssueClassificationResponse:
        issue_classification_request = IssueClassificationRequest(
            issue_id=self.current_issue_id, repository_id=self.current_repository_id
        )
        issue_classification_response: IssueClassificationResponse = (
            self.pipeline.classify_issue(issue_classification_request)
        )
        return issue_classification_response

    def exit_workflow(self) -> None:
        self.pipeline.end()
        Logger.log_end("Workflow Exited")
