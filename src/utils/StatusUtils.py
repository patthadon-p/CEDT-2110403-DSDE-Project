# Import necessary modules
import json

# Import utility functions
from .ConfigUtils import read_config_path


def load_status_mapping(filepath: str = "") -> dict:
    """
    Description:
    Load a JSON file containing the mapping of state values to status values.

    Args:
        filepath (str): Path to the JSON file. If empty, defaults to the path specified in the configuration file.
    """

    filepath = read_config_path(key="status_mapping_path", filepath=filepath)

    with open(filepath, encoding="utf-8") as file:
        status_mapping = json.load(file)

    return status_mapping
