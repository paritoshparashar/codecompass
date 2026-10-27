# function_candidate.py

from pathlib import Path

from ...domain.token_package.token import Token
from .candidate_interface import Candidate


class FunctionCandidate(Candidate):
    def __init__(
        self,
        candidate_id: int,
        file_path: Path,
        function_name: str,
        start_line: int,
        end_line: int,
        tokens: list[Token] | None = None,
    ):
        super().__init__(
            candidate_id=candidate_id,
            filePath=file_path,
            tokens=tokens,
        )
        self.function_name = function_name
        self.start_line = start_line
        self.end_line = end_line
