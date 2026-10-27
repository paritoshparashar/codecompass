__all__ = ["Vocabulary"]
from collections.abc import Sequence

from ...domain.token_package import Token

"""
Still not completely Implemented, do not use this class yet. 
This is a placeholder for the Vocabulary class 
that will be used in the future for localization purposes.
"""


class Vocabulary:
    def __init__(self):
        self._tokens: dict[str, Token] = {}

    def add(self, tokens: Sequence[Token]) -> None:
        for token in tokens:
            self._tokens.setdefault(token.normalized, token)

    def __contains__(self, normalized: str) -> bool:
        return normalized in self._tokens

    def __len__(self) -> int:
        return len(self._tokens)
