__all__ = ("ClassificationService",)

from ...application.classification_package.classification_strategy import (
    ClassificationStrategy,
)
from ...domain.issue import Issue
from ...logger import Logger


class ClassificationService:
    def __init__(self, strategy: ClassificationStrategy):
        self.strategy: ClassificationStrategy = strategy
        self.serviceName: str = "Localization"

    def classify_issue(self, issue: Issue) -> None:
        # Implement classification logic based on the strategy
        Logger.log_service_start(f"{self.serviceName}")
        if self.strategy is None:
            Logger.log_error(ValueError("Classification strategy is not set."))
            Logger.log_service_end(self.serviceName, withError=True)
            return

        self.strategy.classify(issue)
        Logger.log_service_end(self.serviceName, withError=False)