"""
Data loading utility for geographic area names.

This module provides a specialized function to safely load official Bangkok
area names from a configured JSON file, ensuring the file path is correctly
resolved using the project's configuration utilities.

Functions
---------
load_bangkok_official_area_names
    Loads a dictionary of area names from a JSON file, typically used for
    mapping or reference in data processing tasks.
"""

# Import necessary modules
import json

# Import utility functions
from .ConfigUtils import read_config_path


def load_bangkok_official_area_names(filepath: str = "") -> dict:
    """
    Loads official area names for Bangkok from a JSON file.

    The function uses the `read_config_path` utility to locate the path
    to the JSON file. It expects the JSON file to contain a dictionary
    mapping official area codes or identifiers to their names.

    Parameters
    ----------
    filepath : str, optional
        The absolute path to the JSON file. If provided (not empty), this
        path is used directly, overriding the path specified in the config
        file under 'bangkok_official_area_name_path'. Default is "".

    Returns
    -------
    dict
        A dictionary containing the loaded area names (e.g., {'district': ['name1', ...], ...}).

    Raises
    ------
    FileNotFoundError
        If the resolved file path does not exist.
    JSONDecodeError
        If the file content is not valid JSON.

    See Also
    --------
    .ConfigUtils.read_config_path : The utility function used to resolve the path.
    """

    filepath = read_config_path(
        key="bangkok_official_area_name_path", filepath=filepath
    )

    with open(filepath, encoding="utf-8") as file:
        area_names = json.load(file)

    return area_names
