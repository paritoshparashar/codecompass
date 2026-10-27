__all__ = ["RepositoryManager"]
from .repository import Repository


class RepositoryManager:
    def __init__(self):
        self.repositories = {}

    def get_repository(self, repo_id: int) -> Repository:
        return self.repositories.get(repo_id)

    def add_repository(self, repository: Repository) -> None:
        self.repositories[repository.id] = repository
