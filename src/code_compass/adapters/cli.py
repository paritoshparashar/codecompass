from pathlib import Path
from typing import TypeVar

from code_compass.ports.io_objects import (
    InputRequest,
    IssueRequest,
    NextActionRequest,
    URLRequest,
)

T = TypeVar("T", bound=InputRequest)

class CLIAdapter:
    def get_input(self, request: T) -> T:

        if isinstance(request, URLRequest):
            request.url = input("Please enter the repository URL: ").strip()
            request.branch = (input("Enter branch (default: main): ").strip()) or "main"

        elif isinstance(request, IssueRequest):
            request.file_path = Path(
                input("Enter issue description file path: ").strip()
            )

        elif isinstance(request, NextActionRequest):
            print("1. New issue")
            print("2. New repository")
            print("3. Exit")

            choice = input("Choose: ").strip()

            mapping = {
                "1": NextActionRequest.NextAction.NEW_ISSUE,
                "2": NextActionRequest.NextAction.NEW_REPOSITORY,
                "3": NextActionRequest.NextAction.EXIT,
            }

            request.next_action = mapping.get(choice)

        request.set_by_user = self._is_populated(request)

        return request

    @staticmethod
    def _is_populated(request: InputRequest) -> bool:

        if isinstance(request, URLRequest):
            return bool(request.url) and bool(request.branch)

        if isinstance(request, IssueRequest):
            return request.file_path is not None

        if isinstance(request, NextActionRequest):
            return request.next_action is not None

        return False
