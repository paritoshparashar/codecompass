from dataclasses import dataclass

from .localization_level import LocalizationLevel


@dataclass(frozen=True, slots=True)
class LocalizationConfig:
    level: LocalizationLevel = LocalizationLevel.FILE
    strategy: str = "bm25"
    top_k: int = 10

    # BM25 parameters
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    def __post_init__(self) -> None:
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative")

        if self.strategy not in {"bm25"}:
            raise ValueError(f"Unsupported strategy: {self.strategy}")

        if self.bm25_k1 < 0:
            raise ValueError("bm25_k1 must be non-negative")

        if not 0.0 <= self.bm25_b <= 1.0:
            raise ValueError("bm25_b must be between 0 and 1")