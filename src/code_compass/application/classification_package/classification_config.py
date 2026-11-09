__all__ = ("ClassificationConfig", "ClassificationStrategyType")

from dataclasses import dataclass
from enum import Enum, auto


class ClassificationStrategyType(Enum):
    BM25Regression = auto()

@dataclass(frozen=True, slots=True)
class ClassificationConfig:
    strategyType: ClassificationStrategyType = ClassificationStrategyType.BM25Regression
    