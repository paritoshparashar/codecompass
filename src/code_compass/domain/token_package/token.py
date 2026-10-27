__all__ = ("Token",)

from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True, slots=True)
class Token:
    class TokenKind(Enum):
            WORD = auto()
            NUMBER = auto()
            PUNCTUATION = auto()
            SYMBOL = auto()
            
    text: str
    normalized: str
    kind: "Token.TokenKind" = TokenKind.WORD