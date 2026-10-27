from ...domain.token_package.token import Token
from .candidate_interface import Candidate


class FileCandidate(Candidate):
    def __init__(self, candidate_id: int, filePath: str, tokens: list[Token] | None = None,):
        super().__init__(candidate_id, filePath, tokens)