import unittest
from src.repoReader import find_files_with_extension

class TestRepocloner(unittest.TestCase):
    def test_orchestrator(self):
        # Test the find_files_with_extension function
        root = "clonedRepository"
        extension = ".py"
        files = find_files_with_extension(root, extension)
        print(f"{files}")
        assert (type(files) == list)
        assert (type(files[0]) == str)

if __name__ == "__main__":
    unittest.main()