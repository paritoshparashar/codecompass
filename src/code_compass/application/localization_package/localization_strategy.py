from abc import ABC, abstractmethod

from ...domain.candidate_package import Candidate
from ...domain.issue import Issue


class LocalizationStrategy(ABC):
    """
    A protocol for defining localization strategies.
    """
    @abstractmethod
    def localize(self, candidates: list[Candidate], issue: Issue, top_k: int) -> list[Candidate] | None:
        """
        Localizes the given issue within the provided candidates.
        Modifies the candidates in place based on the issue.

        Args:
            repository: The repository to localize the issue in.
            issue: The issue to be localized.
            top_k: The number of top candidates to return.

        Returns:
            A list of top k candidates that are localized based on the issue.
        """
