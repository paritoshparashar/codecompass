
__all__ = ["BM25LocalizationStrategy"]

from ....application.localization_package.localization_strategy import (
    LocalizationStrategy,
)
from ....domain.candidate_package import Candidate
from ....domain.issue import Issue
from .bm25_scorer import BM25Scorer


class BM25LocalizationStrategy(LocalizationStrategy):
    def __init__(self, scorer: BM25Scorer):
        self.bm25_scorer = scorer

    def localize(
        self,
        candidates: list[Candidate],
        issue: Issue,
        top_k: int
    ) -> list[Candidate]:
        if top_k < 0:
            raise ValueError("top_k must be non-negative")

        if not candidates or top_k == 0:
            return []

        scores = self.bm25_scorer.score(candidates, issue)

        ranked = sorted(
            zip(candidates, scores),
            key=lambda item: item[1],
            reverse=True,
        )

        for rank, (candidate, score) in enumerate(ranked, start=1):
            candidate.score = score
            candidate.rank = rank

        return [candidate for candidate, _ in ranked[:top_k]]
