# The application will run from here

import argparse

from .logger import Logger
from .pipeline import (
    CodeCompassPipeline,
    InitializeRepositoryRequest,
    InitializeRepositoryResponse,
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
    if repository_initialization_response.status != ResponseStatus.SUCCESS:
        exit_app(orchestrator)

    # Issue Localization
    issue_localization_response = issue_localization(
        orchestrator, repository_initialization_response
    )
    if issue_localization_response.status != ResponseStatus.SUCCESS:
        exit_app(orchestrator)
    print (f"Localized Candidates: {issue_localization_response.localized_candidates}")

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
    response: InitializeRepositoryResponse = orchestrator.startPipeline(request)
    return response


def issue_localization(
    orchestrator: CodeCompassPipeline, response: InitializeRepositoryResponse
) -> IssueLocalizationResponse:
    issue:str = input("Please enter the issue to localize: ")
    issue_localization_request = IssueLocalizationRequest(
        repository_id=response.repository_id, issue=issue
    )
    issue_localization_response: IssueLocalizationResponse = (
        orchestrator.localize_issue(issue_localization_request)
    )
    return issue_localization_response


def exit_app(orchestrator: CodeCompassPipeline) -> None:
    orchestrator.end()
    Logger.log_end("CodeCompass Exited")


if __name__ == "__main__":
    main()
