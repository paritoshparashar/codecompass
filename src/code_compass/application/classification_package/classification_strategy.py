__all__ = ["ClassificationStrategy"]

from abc import ABC, abstractmethod

from ...domain.issue import Issue, IssueType


class ClassificationStrategy(ABC):
    """
    An abstract base class for classification strategies.
    """

    @abstractmethod
    def classify(self, issue: Issue) -> IssueType:
        """
        Classifies the given issue.

        Args:
            issue: The issue to be classified.

        Returns:
            The classification result for the issue.
        """
