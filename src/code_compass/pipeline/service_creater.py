from pathlib import Path

from ..algorithms.localization.BM25.bm25_localization_strategy import (
    BM25LocalizationStrategy,
    BM25Scorer,
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


class ServiceCreater:
    def __init__(self):
        pass

    def create_initialization_service(self) -> RepositoryInitializationService:
        return RepositoryInitializationService(
            Path(__file__).parents[3] / "clonedRepository"
        )

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

        return LocalizationService(strategy=strategy, loc_level=config.level, top_k=config.top_k)
