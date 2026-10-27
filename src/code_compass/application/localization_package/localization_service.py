__all__ = ["LocalizationService"]


import ast

from ...domain.candidate_package.candidate_interface import Candidate
from ...domain.candidate_package.file_candidate import FileCandidate
from ...domain.candidate_package.function_candidate import FunctionCandidate
from ...domain.issue import Issue
from ...domain.repository_package.repository import Repository
from .localization_config import LocalizationLevel
from .localization_strategy import (
    LocalizationStrategy,
)
from .tokenizer import Tokenizer


class LocalizationService:
    def __init__(self, strategy: LocalizationStrategy, loc_level: LocalizationLevel, top_k: int = 10):
        self.strategy: LocalizationStrategy = strategy
        self.loc_level: LocalizationLevel = loc_level
        self.top_k: int = top_k
        self.tokenizer: Tokenizer = Tokenizer()

    def localize_issue(self, issue: Issue, repository: Repository) -> list[Candidate]:
        """
        Localizes the given issue within the provided repository using the specified strategy.

        Args:
            issue: The issue to be localized.
            repository (Repository): The repository in which to localize the issue.

        Returns:
            list[Candidate]: A list of localized candidates or results based on the strategy.
        """
        if self.strategy is None:
            raise ValueError("Localization strategy is not set.")
        # Get the candidates from the repository
        candidates: list[Candidate] = self.get_candidates(repository, self.loc_level)
        # Tokenize the issue description
        issue.set_tokens(self.tokenizer.tokenize(issue.description))

        # Use the strategy to localize the issue
        candidates = self.strategy.localize(candidates=candidates, issue=issue, top_k=self.top_k)
        self.log_localization_results(candidates)
        return candidates

    def get_candidates(
        self, repository: Repository, loc_level: LocalizationLevel
    ) -> list[Candidate]:
        """
        Retrieves candidates from the repository based on the localization level.

        Args:
            repository (Repository): The repository from which to retrieve candidates.
            loc_level (LocalizationLevel): The level at which to localize the issue.
            Returns:
            list[Candidate]: A list of candidates.
        """
        candidates: list[Candidate] = []
        match loc_level:
            case LocalizationLevel.FILE:
                file_level_candidates = self.handle_file_level_candidates(repository)
                candidates.extend(file_level_candidates)
            case LocalizationLevel.FUNCTION:
                function_level_candidates = self.handle_function_level_candidates(
                    repository
                )
                candidates.extend(function_level_candidates)
            case _:
                raise ValueError(f"Unsupported localization level: {loc_level}")

        return candidates

    def handle_file_level_candidates(
        self, repository: Repository
    ) -> list[FileCandidate]:
        """
        Handles the creation of file-level candidates.

        Args:
            repository (Repository): The repository from which to create file-level candidates.

        Returns:
            list[FileCandidate]: A list of file-level candidates.
        """
        file_candidates: list[FileCandidate] = []
        for document in repository.documents:
            content: str = document.read_content()
            if not content.strip():
                continue  # Skip empty documents
            # Create a FileCandidate for each file
            file_candidate = FileCandidate(
                candidate_id=document.doc_id,
                filePath=document.path,
                tokens=self.tokenizer.tokenize(content),
            )
            file_candidates.append(file_candidate)
        return file_candidates

    def handle_function_level_candidates(
        self, repository: Repository
    ) -> list[FunctionCandidate]:
        """
        Handles the creation of function-level candidates.

        Args:
            repository (Repository): The repository from which to create function-level candidates.

        Returns:
            list[FunctionCandidate]: A list of function-level candidates.
        """
        candidates: list[FunctionCandidate] = []
        next_candidate_id = 0
        for document in repository.documents:
            content: str = document.read_content()
            if not content.strip():
                continue  # Skip empty documents
            if document.path.suffix != ".py":
                continue

            try:
                tree = ast.parse(content, filename=str(document.path))
            except SyntaxError:
                # A file with invalid Python syntax cannot be parsed reliably.
                continue

            lines = content.splitlines()

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                start_line = node.lineno
                end_line = node.end_lineno

                # Extract the source belonging to this function.
                function_source = "\n".join(lines[start_line - 1 : end_line])

                candidates.append(
                    FunctionCandidate(
                        candidate_id=next_candidate_id,
                        file_path=document.path,
                        function_name=node.name,
                        start_line=start_line,
                        end_line=end_line,
                        tokens=self.tokenizer.tokenize(function_source),
                    )
                )
                next_candidate_id += 1

        return candidates

    def log_localization_results(self, candidates: list[Candidate]):
        """
        Logs the results of the localization process.

        Args:
            candidates (list[Candidate]): The list of localized candidates.
        """
        if not candidates:
            print("No candidates were localized.")
            return

        print(f"Localization completed successfully with {len(candidates)} candidates.")
        for candidate in candidates:
            if isinstance(candidate, FileCandidate):
                print(f"File Candidate: {candidate.filePath}")
            elif isinstance(candidate, FunctionCandidate):
                print(
                    f"Function Candidate: {candidate.function_name} in {candidate.filePath} "
                    f"(Lines {candidate.start_line}-{candidate.end_line})"
                )
