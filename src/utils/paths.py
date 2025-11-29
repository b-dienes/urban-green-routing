from pathlib import Path


def get_data_folder(subfolder="raw"):
    """
    Returns the absolute path to a project data subfolder, creating it if necessary.

    This ensures that any module needing to save or read data
    has a reliable, consistent folder to work with, without
    changing the global working directory.

    Args:
        subfolder (str): Name of the subfolder (e.g., "raw", "processed").

    Returns:
        Path: Absolute Path object pointing to the requested folder.
    """
    project_root = Path.home() / "urban-green-routing" / "data"
    folder = project_root / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    print("FOLDER: ", folder)
    #return str(folder)
    return folder
