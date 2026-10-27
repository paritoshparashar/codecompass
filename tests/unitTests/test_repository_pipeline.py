__all__ = [
    "TestDomainRepositoryAndDocument",
    "TestRepoReader",
    "TestRepositoryInitializationService",
]

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_compass.application.initialization_package.repository_reader import RepoReader
from code_compass.application.initialization_package.repostiory_initialization_service import (
    RepositoryInitializationService,
)
from src.code_compass.domain.repository_package import *


class TestDomainRepositoryAndDocument(unittest.TestCase):
    """Tests for Document,
    Repository (immutability + read-only view),
    and RepositoryManager."""

    def test_document_attributes_and_read_content(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.py"
            file_path.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

            doc = Document(
                doc_id=1,
                name="sample.py",
                path=file_path,
                repository_id=42,
            )

            self.assertEqual(doc.doc_id, 1)
            self.assertEqual(doc.name, "sample.py")
            self.assertEqual(doc.path, file_path)
            self.assertEqual(doc.repository_id, 42)
            self.assertIn("def hello():", doc.read_content())

    def test_repository_read_only_documents_and_immutability(self):
        repo_path = Path("/tmp/fake_repo")
        repo = Repository(
            repo_id=101, name="fake_repo", url="https://github.com/a/b", path=repo_path
        )

        # Invariant checks: identity properties
        self.assertEqual(repo.repo_id, 101)
        self.assertEqual(repo.name, "fake_repo")
        self.assertEqual(repo.url, "https://github.com/a/b")
        self.assertEqual(repo.path, repo_path)

        # Documents list starts empty
        self.assertEqual(len(repo.documents), 0)

        # Adding a document works via add_document()
        doc = Document(
            doc_id=1, name="f.py", path=repo_path / "f.py", repository_id=101
        )
        repo.add_document(doc)
        self.assertEqual(len(repo.documents), 1)
        self.assertEqual(repo.documents[0].name, "f.py")

        # Invariant: documents view is strictly read-only (cannot append directly)
        with self.assertRaises(AttributeError):
            repo.documents.append(doc)

    def test_repository_manager_storage_and_retrieval(self):
        manager = RepositoryManager()
        repo = Repository(
            repo_id=202,
            name="test_repo",
            url="https://github.com/x/y",
            path=Path("/tmp/x"),
        )

        self.assertIsNone(manager.get_repository(202))

        manager.add_repository(repo)
        retrieved = manager.get_repository(202)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.repo_id, 202)
        self.assertEqual(retrieved.name, "test_repo")


class TestRepoReader(unittest.TestCase):
    """Tests for recursive directory traversal and directory exclusion."""

    def test_find_files_filters_hidden_and_pycache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            # Normal python files
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print(1)")
            (root / "src" / "utils.py").write_text("print(2)")
            # Non-python file
            (root / "src" / "README.md").write_text("# Readme")
            # Ignored folder (.git)
            (root / ".git").mkdir()
            (root / ".git" / "hidden.py").write_text("secret")
            # Ignored folder (__pycache__)
            (root / "src" / "__pycache__").mkdir()
            (root / "src" / "__pycache__" / "cache.py").write_text("cache")

            reader = RepoReader()
            files = reader.find_files_with_extension(str(root), ".py")

            found_names = [Path(f).name for f in files]
            self.assertIn("main.py", found_names)
            self.assertIn("utils.py", found_names)
            self.assertNotIn("README.md", found_names)
            self.assertNotIn("hidden.py", found_names)
            self.assertNotIn("cache.py", found_names)


class TestRepositoryInitializationService(unittest.TestCase):
    """Tests repository cloning orchestration and document loading (isolated from git network)."""

    def test_validate_github_url(self):
        service = RepositoryInitializationService(root_folder=Path("/tmp"))
        self.assertTrue(service.validate_github_url("https://github.com/user/repo"))
        self.assertTrue(service.validate_github_url("http://github.com/user/repo"))
        self.assertFalse(service.validate_github_url("https://gitlab.com/user/repo"))
        self.assertFalse(service.validate_github_url("not_a_url"))

    @patch.object(RepositoryInitializationService, "clone_repository")
    def test_initialize_repository_flow(self, mock_clone):
        # Mock git clone so we don't hit the internet
        def fake_clone(git_url, branch, destination):
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "app.py").write_text("print('hello')", encoding="utf-8")
            (destination / "test.py").write_text("print('test')", encoding="utf-8")
            return True

        mock_clone.side_effect = fake_clone

        with tempfile.TemporaryDirectory() as tmp_dir:
            service = RepositoryInitializationService(root_folder=Path(tmp_dir))
            repo = service.initialize_repository(
                "https://github.com/test/repo", branch="main"
            )

            # Verify repository entity
            self.assertIsInstance(repo, Repository)
            self.assertEqual(repo.url, "https://github.com/test/repo")
            mock_clone.assert_called_once()

            # Verify that documents were parsed and populated
            doc_names = [doc.name for doc in repo.documents]
            self.assertIn("app.py", doc_names)
            self.assertIn("test.py", doc_names)
            self.assertEqual(len(repo.documents), 2)


if __name__ == "__main__":
    unittest.main()
