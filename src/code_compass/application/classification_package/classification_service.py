__all__ = ("ClassificationService",)


from ...algorithms.classification.BM25_regression_classifier.bm25_reg_strategy import (
    BM25RegStrategy,
)
from ...application.classification_package import (
    ClassificationConfig,
    ClassificationStrategyType,
)
from ...application.service import Service
from ...domain.issue import Issue, IssueType
from ...logger import Logger


class ClassificationService(Service):
    def __init__(self, config: ClassificationConfig):
        # Validated Config - from ServiceCreater
        self.setConfig(config)
        self.serviceName: str = "Classification"

    def setConfig(self, config: ClassificationConfig):
        self.config = config
        match config.strategyType:
            case ClassificationStrategyType.BM25Regression:
                self.strategy = (
                    BM25RegStrategy()
                )  # Replace with actual strategy implementation
            case _:
                raise ValueError(f"Unsupported strategy: {config.strategyType}")

    def logConfig(self):
        # use __repr__() of the Config object to log the config details (TODO)
        Logger.log(f"{self.serviceName} Service Configuration:")
        Logger.log(f"    Strategy Type: {self.config.strategyType}")
        Logger.log("\n")

    def classify_issue(self, issue: Issue) -> IssueType | None:
        # Implement classification logic based on the strategy
        Logger.log_service_start(f"{self.serviceName}")
        self.logConfig()
        if self.strategy is None:
            Logger.log_error(ValueError("Classification strategy is not set."))
            Logger.log_service_end(self.serviceName, withError=True)
            return None

        predictedLabel: IssueType = self.strategy.classify(issue)
        Logger.log(f"Issue classified as: {predictedLabel.name}")
        Logger.log_service_end(self.serviceName, withError=False)
        return predictedLabel