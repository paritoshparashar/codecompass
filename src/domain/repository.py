# Class for representing a repository

from pathlib import Path
from typing import List
from dataclasses import dataclass
from domain.document import Document

@dataclass(frozen = True)
class Repository:
    def __init__(self, repo_id: int, name: str, url: str, path: Path):
        self.repo_id = repo_id
        self.name = name
        self.url = url
        self.path = path
        self.documents = List[Document]()  # List of Document objects associated with this repository

    def __repr__(self):
        return f"Repository(repo_id={self.repo_id}, name={self.name})"