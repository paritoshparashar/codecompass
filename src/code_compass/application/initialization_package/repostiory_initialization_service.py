import subprocess
from pathlib import Path

from ...domain.repository_package import *
from ...logger import Logger
from .repository_reader import RepoReader

__all__ = ["RepositoryInitializationService"]


class RepositoryInitializationService:
    def __init__(self, root_folder: Path) -> None:
        self._root_folder = root_folder

    def initialize_repository(self, git_url: str, branch: str) -> Repository | None:
        Logger.log_start("Repository Initialization Service: Started")
        # Logic to initialize the repository
        if not self._validate_github_url(git_url):
            return self._log_service_end(withError=True)

        # create unique id to store the repository in the system
        repository_id = hash(git_url + branch) % (10**8)
        destination = self._root_folder / str(repository_id)

        destination.parent.mkdir(parents=True, exist_ok=True)
        # clone the repository using git
        if not self._clone_repository(git_url, branch, destination):
            return self._log_service_end(withError=True)

        repository = Repository(
            id=repository_id,
            name=git_url.split("/")[-1],  # extracting the repo name from the URL
            url=git_url,
            path=destination,
        )

        # Initialize the repo for the system
        if not self._initialize_repository(repository):
            return self._log_service_end(withError=True)

        self._log_service_end(withError=False)
        return repository

    def _initialize_repository(self, repository: Repository) -> bool:
        """
        Perform initialization after cloning.

        This is where you can later:
        - read repository files
        - build the BM25 index
        - build an embedding index
        - build a symbol index
        - store repository metadata

        ~ basically prepare the repository for the localization and analysis tasks
        """
        Logger.log(
            f"Initializing Repository...\nRepository Name: {repository.name}\nId:{repository.id}"
        )
        try:
            reader = RepoReader()
            python_files = reader.find_files_with_extension(repository.path, ".py")

            # Create Document objects for each Python file and add them to the repository
            for file_path in python_files:
                # hash would be unique due to unique repo path (present in the file_path)
                document_id = hash(file_path) % (10**8)
                document = Document(
                    doc_id=document_id,
                    name=Path(file_path).name,
                    path=Path(file_path),
                    repository_id=repository.id,
                )
                repository.add_document(document)
        except (OSError, TypeError, ValueError) as e:
            Logger.log(f"{Logger.red('Failed')} {e}")
            return False
        Logger.log(f"{Logger.green('Successful')}")
        return True

    def _validate_github_url(self, git_url: str) -> bool:
        # Logic to validate the GitHub URL
        valid_prefixes = ("https://github.com/", "http://github.com/")

        if not git_url.startswith(valid_prefixes):
            Logger.log(
                f"Validating GitHub URL...\n'{git_url}': {Logger.red('Invalid (Prefix)')}\n"
            )
            return False
        Logger.log(f"GitHub URL '{git_url}': {Logger.green('Valid')}\n")
        return True

    def _clone_repository(self, git_url: str, branch: str, destination: Path) -> bool:
        Logger.log(
            f"Cloning Repository...\nfrom URL: {git_url}\nto destination: {destination.relative_to(Path.cwd())}"
        )
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
            Logger.log(f"{Logger.green('Successful')}\n")
            return True
        except subprocess.CalledProcessError as e:
            Logger.log_end(f"{Logger.red('Failed')}: {e.stderr}")
            return False

    def _log_service_end(self, withError: bool) -> None:
        if withError:
            Logger.log_end(
                f"Repository Initialization Service: {Logger.red('Exited with Error')}"
            )
        else:
            Logger.log_end(
                f"Repository Initialization Service: {Logger.green('Exited Successfully')}"
            )
