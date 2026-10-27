import re
from enum import Enum

from ...domain.repository_package import Document
from ...domain.token_package import Token


class Tokenizer:
    def __init__(self):
        self.vocabulary = set()
        self._train_vocabulary([])

    class StringType(Enum):
        SNAKE_CASE = r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$"
        CAMEL_CASE = r"^[a-z]+(?:[A-Z][a-z0-9]*)+$"
        PASCAL_CASE = r"^(?:[A-Z][a-z0-9]*){2,}$"
        UNKNOWN = r"^.*$"  # Fallback for any other format

    def tokenize(self, text: str) -> list[Token]:
        self.result = set()
        # Tokenize the input text into tokens, handling camelCase, pascalCase, and snake_case
        # First split by whitespace and underscores, then handle camelCase and pascalCase
        tokens = re.findall(r"\S+", text)
        # identify the tokens that are camelCase or pascalCase and split them further
        for token in tokens:
            current: list[Token] = []
            match self.token_type(token):
                case Tokenizer.StringType.SNAKE_CASE:
                    current = [
                        self.create_token(t) for t in self.snake_case_split(token)
                    ]
                case Tokenizer.StringType.CAMEL_CASE:
                    current = [
                        self.create_token(t) for t in self.camel_case_split(token)
                    ]
                case Tokenizer.StringType.PASCAL_CASE:
                    current = [
                        self.create_token(t) for t in self.pascal_case_split(token)
                    ]
                case _:
                    pass  # Do nothing for unknown types

            self.result.update(current)
            # add the original token as well
            self.result.update([self.create_token(token)])
        return list(self.result)

    @staticmethod
    def token_type(token: str) -> "Tokenizer.StringType | None":
        if re.fullmatch(Tokenizer.StringType.SNAKE_CASE.value, token):
            return Tokenizer.StringType.SNAKE_CASE
        elif re.fullmatch(Tokenizer.StringType.CAMEL_CASE.value, token):
            return Tokenizer.StringType.CAMEL_CASE
        elif re.fullmatch(Tokenizer.StringType.PASCAL_CASE.value, token):
            return Tokenizer.StringType.PASCAL_CASE
        else:
            return Tokenizer.StringType.UNKNOWN

    def create_token(self, text: str) -> Token:
        normalized = text.lower()
        return Token(text=text, normalized=normalized, kind=Token.TokenKind.WORD)

    def snake_case_split(self, identifier: str) -> list[str]:
        return identifier.split("_")

    def camel_case_split(self, identifier: str) -> list[str]:
        return re.split(r"(?<=[a-z0-9])(?=[A-Z])", identifier)

    def pascal_case_split(self, identifier: str) -> list[str]:
        return re.split(r"(?<=[a-z0-9])(?=[A-Z])", identifier)

    def _train_vocabulary(self, documents: list[Document]) -> None:
        # for document in documents:
        #     tokens = self.tokenize(document.read_content())
        #     self.vocabulary.update(tokens)
        pass  # Placeholder for training vocabulary from documents
