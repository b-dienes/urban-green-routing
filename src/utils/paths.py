import logging
from pathlib import Path


logger = logging.getLogger(__name__)

def get_data_folder(subfolder: str = "raw") -> Path:
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

    logger.info("Data folder path: %s", folder)

    return folder
