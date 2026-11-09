from enum import Enum, auto
from pathlib import Path

from ..algorithms.classification.BM25_regression_classifier.bm25_reg_strategy import (
    BM25RegStrategy,
)
from ..algorithms.localization.BM25.bm25_localization_strategy import (
    BM25LocalizationStrategy,
    BM25Scorer,
)
from ..application.classification_package import (
    ClassificationConfig,
    ClassificationService,
    ClassificationStrategyType,
)
from ..application.initialization_package.repostiory_initialization_service import (
    RepositoryInitializationService,
)
from ..application.localization_package.localization_config import (
    LocalizationConfig,
    LocalizationLevel,
    LocalizationStrategyType,
)
from ..application.localization_package.localization_service import LocalizationService


class ServiceType(Enum):
    INITIALIZATION = auto()
    LOCALIZATION = auto()
    CLASSIFICATION = auto()

class ServiceCreater:
    def __init__(self):
        pass

    def create_initialization_service(self) -> RepositoryInitializationService:
        service = RepositoryInitializationService(
            Path(__file__).parents[3] / "clonedRepository"
        )
        return service

    def create_localization_service(self) -> LocalizationService:
        # create the LocalizationConfig object
        config = LocalizationConfig(
            level=LocalizationLevel.FUNCTION,
            strategy=LocalizationStrategyType.BM25,
            top_k=10,
            bm25_k1=1.5,
            bm25_b=0.75,
        )

        match config.strategy:
            case LocalizationStrategyType.BM25:
                scorer = BM25Scorer(
                    k1=config.bm25_k1, b=config.bm25_b
                )
                strategy = BM25LocalizationStrategy(scorer=scorer)
            case _:
                raise ValueError(f"Unsupported strategy: {config.strategy}")

        service = LocalizationService(strategy=strategy, loc_level=config.level, top_k=config.top_k)
        return service

    def create_classification_service(self) -> ClassificationService:
        # For now, we can hardcode the strategy. In a real-world scenario, this could be configurable.
        config = ClassificationConfig(
                    strategyType=ClassificationStrategyType.BM25Regression,
                )
        return ClassificationService(config=config)