
from collections import Counter
from math import log

from ....domain.candidate_package import Candidate
from ....domain.issue import Issue
from ....domain.token_package.token import Token


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
        documents: list[Candidate],
        issue: Issue,
    ) -> list[float]:
        """Return one BM25 score for each document."""
        if not documents:
            return []

        query_tokens = {
            token for token in issue.issueTokens if token
        }

        term_frequencies = [
            Counter(token for token in doc.tokens if token)
            for doc in documents
        ]

        document_lengths = [
            sum(frequencies.values())
            for frequencies in term_frequencies
        ]

        average_document_length = (
            sum(document_lengths) / len(documents)
        )

        document_frequency = Counter()
        for frequencies in term_frequencies:
            document_frequency.update(frequencies.keys())

        # Corpus-level calculation: performed once.
        idf_scores = self._calculate_idf(
            query_tokens,
            document_frequency,
            len(documents),
        )

        # Document-level calculation: performed once per document.
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
        query_tokens: set[Token],
        document_frequency: Counter[Token],
        total_documents: int,
    ) -> dict[Token, float]:
        """Calculate IDF for every query token across the corpus."""
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
        """Calculate BM25's normalized term-frequency contribution."""
        if frequency == 0 or average_document_length == 0:
            return 0.0

        length_normalization = (
            1.0 - self.b
            + self.b * document_length / average_document_length
        )

        return (
            frequency * (self.k1 + 1.0)
            / (frequency + self.k1 * length_normalization)
        )

    def _score_document(
        self,
        query_tokens: set[Token],
        term_frequencies: Counter[Token],
        document_length: int,
        average_document_length: float,
        idf_scores: dict[Token, float],
    ) -> float:
        """Combine each query token's TF and IDF into one document score."""
        score = 0.0

        for token in query_tokens:
            tf_score = self._calculate_tf(
                term_frequencies[token],
                document_length,
                average_document_length,
            )

            score += idf_scores[token] * tf_score

        return score
