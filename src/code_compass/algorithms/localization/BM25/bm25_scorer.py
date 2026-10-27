from collections import Counter
from math import log

from ....domain.candidate_package import Candidate
from ....domain.issue import Issue


class BM25Scorer:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        if k1 < 0:
            raise ValueError("k1 must be non-negative")
        if not 0.0 <= b <= 1.0:
            raise ValueError("b must be between 0 and 1")

        self.k1 = k1
        self.b = b

    def score(
        self,
        candidates: list[Candidate],
        issue: Issue,
    ) -> list[float]:
        """Return one BM25 score for each candidate."""
        if not candidates:
            return []

        query_tokens = {
            token.normalized for token in issue.get_tokens() if token.normalized
        }

        term_frequencies = [
            Counter(token.normalized for token in candidate.tokens if token.normalized)
            for candidate in candidates
        ]

        document_lengths = [
            sum(frequencies.values()) for frequencies in term_frequencies
        ]

        average_document_length = sum(document_lengths) / len(candidates)

        document_frequency: Counter[str] = Counter()

        for frequencies in term_frequencies:
            # Each normalized term contributes at most once per candidate.
            document_frequency.update(frequencies.keys())

        idf_scores = self._calculate_idf(
            query_tokens,
            document_frequency,
            len(candidates),
        )

        return [
            self._score_document(
                query_tokens,
                frequencies,
                document_length,
                average_document_length,
                idf_scores,
            )
            for frequencies, document_length in zip(
                term_frequencies,
                document_lengths,
            )
        ]

    def _calculate_idf(
        self,
        query_tokens: set[str],
        document_frequency: Counter[str],
        total_documents: int,
    ) -> dict[str, float]:
        """Calculate IDF for each query term across the corpus."""
        return {
            token: log(
                1.0
                + (total_documents - document_frequency[token] + 0.5)
                / (document_frequency[token] + 0.5)
            )
            for token in query_tokens
        }

    def _calculate_tf(
        self,
        frequency: int,
        document_length: int,
        average_document_length: float,
    ) -> float:
        """Calculate BM25's length-normalized term-frequency contribution."""
        if frequency == 0 or average_document_length == 0:
            return 0.0

        length_normalization = (
            1.0 - self.b + self.b * document_length / average_document_length
        )

        return (
            frequency * (self.k1 + 1.0) / (frequency + self.k1 * length_normalization)
        )

    def _score_document(
        self,
        query_tokens: set[str],
        term_frequencies: Counter[str],
        document_length: int,
        average_document_length: float,
        idf_scores: dict[str, float],
    ) -> float:
        """Combine the TF and IDF contributions for one candidate."""
        score = 0.0

        for token in query_tokens:
            tf_score = self._calculate_tf(
                term_frequencies[token],
                document_length,
                average_document_length,
            )

            score += idf_scores[token] * tf_score

        return score
