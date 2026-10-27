__all__ = ["Candidate"]

from abc import ABC
from pathlib import Path

from ...domain.token_package.token import Token

"""
A protocol for defining candidate objects.
"""


class Candidate(ABC):
    def __init__(
        self,
        candidate_id: int,
        filePath: Path,
        tokens: list[Token] | None = None,
        rank: int = 0,
        score: float = 0.0,
    ):
        self.candidate_id = candidate_id
        self.tokens = [] if tokens is None else tokens
        self.filePath = filePath
        self.rank = rank
        self.score = score
