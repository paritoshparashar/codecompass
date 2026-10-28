
__all__ = ["BM25LocalizationStrategy"]

from ....application.localization_package.localization_strategy import (
    LocalizationStrategy,
)
from ....domain.candidate_package import Candidate
from ....domain.issue import Issue
from ....logger import Logger
from .bm25_scorer import BM25Scorer


class BM25LocalizationStrategy(LocalizationStrategy):
    def __init__(self, scorer: BM25Scorer):
        self.bm25_scorer = scorer

    def localize(
        self,
        candidates: list[Candidate],
        issue: Issue,
        top_k: int
    ) -> list[Candidate] | None:
        if top_k < 0:
            Logger.log_failed(ValueError("top_k must be non-negative"))
            return None

        if not candidates or top_k == 0:
            return []

        Logger.log_start("Localizing Issue using BM25 strategy.../n")

        scores = self.bm25_scorer.score(candidates, issue)

        ranked = sorted(
            zip(candidates, scores),
            key=lambda item: item[1],
            reverse=True,
        )

        for rank, (candidate, score) in enumerate(ranked, start=1):
            candidate.score = score
            candidate.rank = rank

        Logger.log_success(f"Top {top_k} candidates localized using BM25 strategy.")
        Logger.log_end("BM25 Localization Strategy: Completed")
        return [candidate for candidate, _ in ranked[:top_k]]
