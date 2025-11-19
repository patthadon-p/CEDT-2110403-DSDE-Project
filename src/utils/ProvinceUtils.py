# Import necessary modules
import json

# Import utility functions
from src.utils.ConfigUtils import read_config_path

# Get the absolute path to the configs directory
from utils import configs_path


def load_province_whitelist(filepath: str = "") -> dict:
    """
    Description:
    Load a JSON file containing a whitelist of valid province names.

    Args:
        filepath (str): Path to the JSON file. If empty, defaults to the path specified in the configuration file.
    """

    filepath = read_config_path(
        configs_path, key="province_whitelist_path", filepath=filepath
    )

    with open(filepath, encoding="utf-8") as file:
        provinces = json.load(file)

    whitelist = {}
    for standard_name, variants in provinces.items():
        for name in variants:
            whitelist[name] = standard_name

    return whitelist
