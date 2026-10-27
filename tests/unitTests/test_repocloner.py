__all__ = ["TestReader"]
import unittest

from code_compass.application.initialization_package.repository_reader import RepoReader


class TestReader(unittest.TestCase):
    def setUp(self):
        # Setup code before each test method
        self.repoReader = RepoReader()

    def test_orchestrator(self):
        # Test the find_files_with_extension function
        root = "clonedRepository"
        extension = ".py"
        files = self.repoReader.find_files_with_extension(root, extension)
        print(f"{files}")
        assert type(files) == list
        assert type(files[0]) == str


if __name__ == "__main__":
    unittest.main()
