__all__ = ["TestReader"]
import tempfile
import unittest
from pathlib import Path

from code_compass.application.initialization_package.repository_reader import RepoReader


class TestReader(unittest.TestCase):
    def setUp(self):
        self.repoReader = RepoReader()

    def test_find_files_with_extension(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "test1.py").write_text("x = 1")
            (root / "test2.py").write_text("y = 2")
            (root / "doc.txt").write_text("hello")

            files = self.repoReader.find_files_with_extension(str(root), ".py")
            self.assertEqual(len(files), 2)
            self.assertTrue(all(type(f) is str and f.endswith(".py") for f in files))


if __name__ == "__main__":
    unittest.main()
