from pathlib import Path
from application.initialization.repoReader import RepoReader
from domain.repository import Repository
from domain.document import Document
import subprocess
from beautify import Beautify

__all__ = ["RepositoryInitializationService"]

class RepositoryInitializationService :
    def __init__(self, root_folder: Path) -> None:
        self._root_folder = root_folder

    def initialize_repository(self, git_url: str, branch: str) -> Repository | None:
        Beautify.log_start("Repository Inititalization Service Started")
        # Logic to initialize the repository
        if (not self.validate_github_url(git_url)):
            Beautify.log_end(f"Invalid GitHub URL: {git_url}")
            return None

        # create unique id to store the repository in the system
        repository_id = hash(git_url + branch) % (10 ** 8)
        destination = self._root_folder / str(repository_id)

        destination.parent.mkdir(parents=True, exist_ok=True)

        # clone the repository using git
        if not self.clone_repository(git_url, branch, destination):
            Beautify.log_end(f"Failed to clone repository from URL: {git_url}")
            return None

        repository = Repository(
                    repo_id = repository_id,
                    name = destination.name,
                    url = git_url,
                    path = destination
                )

        # Initialize the repo for the system
        self._initialize_repository(repository)
        # create the repository object and return it
        Beautify.log_end(f"Repository Initialization Response: {repository.message}")
        return repository

    def _initialize_repository(self, repository: Repository) -> None :
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
        reader = RepoReader()
        python_files = reader.find_files_with_extension(repository.path, ".py")

        # Create Document objects for each Python file and add them to the repository
        for file_path in python_files:
            # hash would be unique due to unique repo path (present in the file_path)
            document_id = hash(file_path) % (10 ** 8)
            document = Document(
                doc_id=document_id,
                name=Path(file_path).name,
                path=Path(file_path),
                repository_id=repository.repo_id
            )
            repository.add_document(document)

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
        # print new line 
        Beautify.print_start_separator()
        print ("Cloning repository","\nfrom URL:", git_url, "\nto destination:", destination)
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
            print("Repository cloned successfully")
            Beautify.print_end_separator()
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            return False
