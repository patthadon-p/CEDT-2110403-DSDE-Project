"""
Data loading utilities for status and state mappings.

This module provides a function to securely load critical lookup dictionaries
from a JSON configuration file, ensuring consistent translation of raw data
state values into standardized status labels within the data science pipeline.

Functions
---------
load_status_mapping
    Loads a dictionary used for mapping state values (from raw data)
    to standardized status values.
"""

# Import necessary modules
import json

# Import utility functions
from .ConfigUtils import read_config_path


def load_status_mapping(filepath: str = "") -> dict:
    """
    Loads a dictionary mapping state values to standardized status values.

    This function retrieves the file path using the key 'status_mapping_path'
    from the project's configuration utility. It reads the JSON file which is
    expected to contain a dictionary defining the translation logic.

    Parameters
    ----------
    filepath : str, optional
        The absolute path to the JSON file containing the status mapping.
        If provided (not empty), this path overrides the path specified
        in the config file. Default is "".

    Returns
    -------
    dict of {str: str} or {str: list}
        A dictionary containing the loaded mapping (e.g., {'raw_state_1': 'STANDARD_STATUS'}).

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

    filepath = read_config_path(key="status_mapping_path", filepath=filepath)

    with open(filepath, encoding="utf-8") as file:
        status_mapping = json.load(file)

    return status_mapping
