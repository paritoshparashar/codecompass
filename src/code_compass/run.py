# The application will run from here

import argparse
from pathlib import Path

from .logger import Logger
from .pipeline import (
    CodeCompassPipeline,
    InitializeRepositoryRequest,
    InitializeRepositoryResponse,
    IssueClassificationRequest,
    IssueClassificationResponse,
    IssueLocalizationRequest,
    IssueLocalizationResponse,
    ResponseStatus,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code_compass",
        description="A tool for analyzing and localizing code repositories",
    )

    return parser


def main() -> None:
    # Call the orchestrator function
    Logger.log_start("Welcome to Code Compass!")
    orchestrator = CodeCompassPipeline()

    # Repository Initialization
    repository_initialization_response = repostiroy_initialization(orchestrator)
    if (
        repository_initialization_response.status != ResponseStatus.SUCCESS
        or repository_initialization_response.repository_id is None
    ):
        return exit_app(orchestrator)

    current_repository_id: int = repository_initialization_response.repository_id

    # Issue Localization
    issue_localization_response = issue_localization(
        orchestrator, current_repository_id
    )
    if (
        issue_localization_response.status != ResponseStatus.SUCCESS
        or issue_localization_response.issue_id is None
    ):
        return exit_app(orchestrator)

    current_issue_id: int = issue_localization_response.issue_id

    # Issue Classification
    issue_classification_response = issue_classification(
        orchestrator, repository_id=current_repository_id, issue_id=current_issue_id
    )
    if (
        issue_classification_response.status != ResponseStatus.SUCCESS
        or issue_classification_response.classification_result is None
    ):
        return exit_app(orchestrator)

    issue_type = issue_classification_response.classification_result
    Logger.log(
        f"\nIssue Classification Result: The issue has been classified as '{issue_type.name}'."
    )

    # Other operations later
    exit_app(orchestrator)


def repostiroy_initialization(
    orchestrator: CodeCompassPipeline,
) -> InitializeRepositoryResponse:
    github_url: str = input("Please enter the URL of the repository to analyze: ")
    branch_to_analyze = (
        input("Please enter the branch to analyze (default is 'main'): ") or "main"
    )
    request = InitializeRepositoryRequest(git_url=github_url, branch=branch_to_analyze)
    response: InitializeRepositoryResponse = (
        orchestrator.create_and_initialize_repository(request)
    )
    return response


def issue_localization(
    orchestrator: CodeCompassPipeline, repository_id: int
) -> IssueLocalizationResponse:
    # Create a file to store the issue description at the specified Path
    repo_issue_folder = Path("issuesDirectory") / f"issues_for_repo_{repository_id}"
    repo_issue_folder.mkdir(parents=True, exist_ok=True)
    issueFilePath = repo_issue_folder / "issue_description.txt"
    issueFilePath.touch(exist_ok=True)
    Logger.log(
        f"\nAn 'issue_description.txt' file has been created at {issueFilePath}. \nPlease enter the issue description in the file, save it, and close the file when done.\n"
    )
    # ask the user y/n if they want to continue after entering the issue description
    input("Press Enter to continue after entering the issue description in the file...")
    issue: str = issueFilePath.read_text()

    issue_localization_request = IssueLocalizationRequest(
        repository_id=repository_id, issue=issue
    )
    issue_localization_response: IssueLocalizationResponse = (
        orchestrator.localize_issue(issue_localization_request)
    )
    return issue_localization_response


def issue_classification(
    orchestrator: CodeCompassPipeline,
    issue_id: int,
    repository_id: int,
) -> IssueClassificationResponse:
    issue_classification_request = IssueClassificationRequest(
        issue_id=issue_id, repository_id=repository_id
    )
    issue_classification_response: IssueClassificationResponse = (
        orchestrator.classify_issue(issue_classification_request)
    )
    return issue_classification_response


def exit_app(orchestrator: CodeCompassPipeline) -> None:
    orchestrator.end()
    Logger.log_end("CodeCompass Exited")


if __name__ == "__main__":
    main()
