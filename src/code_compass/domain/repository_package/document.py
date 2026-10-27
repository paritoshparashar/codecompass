__all__ = ["Document"]
from pathlib import Path

from ..types import ExtensionType


class Document:
    def __init__(self, doc_id: int, name: str, path: Path, repository_id: int):
        self.doc_id = doc_id
        self.name = name
        self.path = path
        self.repository_id = repository_id
        self.documentExtension: ExtensionType = (
            None  # Placeholder for document extension
        )

    def read_content(self) -> str:
        """
        Read the content of the document.

        Returns
        -------
        str
            Content of the document as a string.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return file.read()
        except (OSError, UnicodeError) as e:
            print(f"Error reading file {self.path}: {e}")
            return ""

    def __repr__(self):
        return f"Document(doc_id={self.doc_id}, name={self.name})"
