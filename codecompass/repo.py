import os
import git
from pathlib import Path
import logging
from typing import List, Optional

# Setup structured logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class RepoIngestionPipeline:
    """
    Manages the end-to-end ingestion pipeline for a GitHub repository.
    Designed as a stateful pipeline: Initialize -> Clone -> Extract -> Yield Files.
    """

    # Directories to strictly ignore to maintain parsing performance and relevance
    IGNORE_DIRS: set = {
        '.git', '__pycache__', 'venv', 'env', 'node_modules', 
        '.tox', 'build', 'dist', '.mypy_cache', '.pytest_cache',
        'tests', 'test', 'docs', 'examples', 'migrations'
    }

    def __init__(self, repo_url: str, target_base_dir: str = "./_repos"):
        """
        Initializes the pipeline with repository details.
        
        :param repo_url: The HTTPS URL of the GitHub repository.
        :param target_base_dir: The base directory to store cloned repositories.
        """
        self.repo_url = repo_url
        self.target_base_dir = Path(target_base_dir)
        
        # State management
        self._repo_name = self._extract_repo_name()
        self._local_path: Optional[Path] = None
        self._extracted_files: List[Path] = []

    def _extract_repo_name(self) -> str:
        """Safely extracts the repository name from the GitHub URL."""
        name = self.repo_url.rstrip('/').split('/')[-1]
        return name[:-4] if name.endswith('.git') else name

    def step_1_clone(self) -> Path:
        """
        Pipeline Step 1: Clones the repository or updates it if it exists.
        Sets the internal _local_path state.
        
        :return: The absolute Path to the local repository directory.
        """
        self.target_base_dir.mkdir(parents=True, exist_ok=True)
        self._local_path = self.target_base_dir / self._repo_name

        if self._local_path.exists():
            logger.info(f"Repo exists at {self._local_path}. Pulling latest changes...")
            try:
                repo = git.Repo(self._local_path)
                repo.remotes.origin.pull()
            except Exception as e:
                logger.warning(f"Failed to pull updates: {e}. Proceeding with existing state.")
        else:
            logger.info(f"Cloning {self.repo_url} into {self._local_path}...")
            git.Repo.clone_from(self.repo_url, self._local_path)

        return self._local_path

    def step_2_extract_files(self) -> List[Path]:
        """
        Pipeline Step 2: Walks the directory tree and extracts relevant Python files.
        Prunes the search space for maximum performance on large codebases.
        
        :return: A list of Path objects pointing to Python files.
        """
        if not self._local_path or not self._local_path.exists():
            raise RuntimeError("Cannot extract files: Pipeline Step 1 (Clone) has not been executed.")

        python_files = []
        
        for root, dirs, files in os.walk(self._local_path):
            # In-place pruning of the directory tree (critical for performance)
            dirs[:] = [
                d for d in dirs 
                if d not in self.IGNORE_DIRS and not d.startswith('.')
            ]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        self._extracted_files = python_files
        logger.info(f"Extraction complete. Found {len(self._extracted_files)} Python files.")
        return self._extracted_files

    def get_files(self) -> List[Path]:
        """Public getter for the extracted files."""
        if not self._extracted_files:
            logger.warning("File list is empty. Did you run step_2_extract_files()?")
        return self._extracted_files

    def execute(self) -> List[Path]:
        """
        Executes the full pipeline sequentially.
        
        :return: The final list of extracted Python files.
        """
        logger.info(f"Starting ingestion pipeline for: {self.repo_url}")
        self.step_1_clone()
        files = self.step_2_extract_files()
        logger.info("Ingestion pipeline finished successfully.")
        return files