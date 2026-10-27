import os

__all__ = ["RepoReader"]


class RepoReader:
    """
    A class to read files from a repository.
    """

    def __init__(self):
        pass

    def find_files_with_extension(self, root, extension) -> list[str]:
        """
        Find all files under a directory with the given extension.

        Parameters
        ----------
        root : str
            Search directory
        extension : str
            File extension

        Returns
        -------
        list[str]
            Matching file paths
        Raises
        ------
        FileNotFoundError
            If the root directory does not exist
        """
        files = []
        if not os.path.exists(root):
            raise FileNotFoundError("Root directory does not exist.")
        for dirpath, dirname, filenames in os.walk(root):
            dirname[:] = [
                d
                for d in dirname
                if not d.startswith(".") and not d.startswith("__pycache__")
            ]
            for filename in filenames:
                if not filename.endswith(extension):
                    continue
                files.append(os.path.join(dirpath, filename))

        return files
