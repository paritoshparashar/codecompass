__all__ = ["LocalizationService"]

from ...domain.candidate_package.candidate_interface import Candidate
from ...domain.repository_package.repository import Repository
from .localization_strategy import (
    LocalizationStrategy,
)


class LocalizationService:
    def __init__(self, strategy: LocalizationStrategy):
        self.strategy = strategy

    def localize_issue(self, issue, repository: Repository) -> list[Candidate]:
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
        candidates = self.get_candidates(repository)

        # Use the strategy to localize the issue
        return self.strategy.localize(candidates=candidates, issue=issue)

    def get_candidates(self, repository: Repository) -> list[Candidate]:
        """
        Retrieves candidates from the repository based on the issue.

        Args:
            issue: The issue for which candidates are to be retrieved.
            repository (Repository): The repository from which to retrieve candidates.
            Returns:
            list[Candidate]: A list of candidates.
        """
        # Placeholder implementation - replace with actual candidate retrieval logic
        return []
