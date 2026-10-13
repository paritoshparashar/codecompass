import os

def find_files_with_extension(root, extension) -> list[str]: 
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
        for filename in filenames:
            if not filename.endswith(extension):
                continue
            files.append(os.path.join(dirpath, filename))
    return files