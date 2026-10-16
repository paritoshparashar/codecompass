class Document:
    def __init__(self, doc_id: int, name: str, path: Path, repository_id: int):
        self.doc_id = doc_id
        self.name = name
        self.path = path
        self.repository_id = repository_id

    def __repr__(self):
        return f"Document(doc_id={self.doc_id}, name={self.name})"