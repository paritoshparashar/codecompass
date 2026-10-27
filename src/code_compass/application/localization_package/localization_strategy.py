from typing import Protocol

from ...domain.candidate_package import Candidate
from ...domain.issue import Issue


class LocalizationStrategy(Protocol):
    """
    A protocol for defining localization strategies.
    """

    def localize(self, candidates: list[Candidate], issue: Issue, top_k: int = 10) -> list[Candidate]:
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
