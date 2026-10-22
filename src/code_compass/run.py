# The application will run from here

import argparse
from pathlib import Path
import pipeline
from pipeline.io_module import InitializeRepositoryRequest, InitializeRepositoryResponse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code_compass",
        description="A tool for analyzing and localizing code repositories",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Replace this with your actual application logic.
    # Call the orchestrator function
    github_url : str = input("Please enter the URL of the repository to analyze: ")
    branch_to_analyze = input("Please enter the branch to analyze (default is 'main'): ") or "main"
    initialize_request = InitializeRepositoryRequest(git_url=github_url, branch=branch_to_analyze)

    orchestrator = pipeline.CodeCompassPipeline()
    response : InitializeRepositoryResponse = orchestrator.startPipeline(initialize_request)
    orchestrator.end()
    return None
    
if __name__ == "__main__":
    main()