from pathlib import Path
from src.domain.repository import Repository
import subprocess

class RepositoryInitializationService :
    def __init__(self, root_folder: Path) -> None:
        self._root_folder = root_folder

    def initialize_repository(self, git_url: str, branch: str) -> Repository:
        # Logic to initialize the repository
        if (not self.validate_github_url(git_url)):
            return None

        # create unique id to store the repository in the system
        repository_id = hash(git_url + branch) % (10 ** 8)
        destination = self._root_folder / str(repository_id)

        destination.parent.mkdir(parents=True, exist_ok=True)

        # clone the repository using git
        if not self.clone_repository(git_url, branch, destination):
            return None

        # Initialize the repo for the system
        self._initialize_repository()

        # create the repository object and return it
        return Repository(
                    repo_id = repository_id,
                    name = destination.name,
                    url = git_url,
                    path = destination
                )

    def _initialize_repository(self) -> None :
        """
        Perform initialization after cloning.

        This is where you can later:
        - read repository files
        - build the BM25 index
        - build an embedding index
        - build a symbol index
        - store repository metadata
        """
        pass

    def validate_github_url(self, git_url: str) -> bool:
        # Logic to validate the GitHub URL
        valid_prefixes = (
            "https://github.com/",
            "http://github.com/"
        )

        if not git_url.startswith(valid_prefixes):
            return False
        return True

    def clone_repository(self, git_url: str, branch: str, destination: Path) -> bool:
        # Logic to clone the repository using git
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--branch",
                    branch,
                    git_url,
                    str(destination),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            return False
