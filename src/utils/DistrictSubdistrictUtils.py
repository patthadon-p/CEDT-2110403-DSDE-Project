# Import necessary modules
import json

# Import utility functions
from src.utils.ConfigUtils import read_config_path

# Get the absolute path to the configs directory
from utils import configs_path


def load_bangkok_official_area_names(filepath: str = "") -> dict:
    """
    Description:
    Load a JSON file containing the official names of districts and subdistricts in Bangkok.

    Args:
        filepath (str): Path to the JSON file. If empty, defaults to the path specified in the configuration file.
    """
    filepath = read_config_path(
        configs_path, key="bangkok_official_area_name_path", filepath=filepath
    )

    with open(filepath, encoding="utf-8") as file:
        area_names = json.load(file)

    return area_names
