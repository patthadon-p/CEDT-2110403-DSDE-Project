"""
Utilities for configuration file path management.

This module provides essential functions for locating the project's main
configuration file ('configs.yaml') and resolving file paths defined within
it to absolute paths. This ensures consistent and reliable file access
across different deployment and development environments in the data science pipeline.

Functions
---------
get_configs_path
    Returns the absolute path to the main 'configs.yaml' file.
read_config_path
    Reads a file path from the config file using a key, and resolves it
    to an absolute path relative to the config file's location.
"""

# Import necessary modules
import os
from pathlib import Path

import yaml


# Define the path to the configs directory
def get_configs_path() -> str:
    """
    Determines the absolute path to the main configuration file.

    It assumes the structure is: /configs/configs.yaml,
    and the utility function is located in /src/utils/config_utils.py.

    Returns
    -------
    str
        The absolute path to the 'configs.yaml' file.
    """

    base_dir = Path(__file__).resolve().parents[2]
    configs_path = base_dir / "configs" / "configs.yaml"
    return str(configs_path)


def read_config_path(key: str, filepath: str = "") -> str:
    """
    Reads a file path from the config file and resolves it to an absolute path.

    If `filepath` is provided, it is returned directly. Otherwise, it loads
    the path from the 'configs.yaml' file using the provided dictionary key.
    It automatically converts relative paths to absolute paths based on the
    location of the 'configs.yaml' file.

    Parameters
    ----------
    key : str
        The dictionary key to look up the path in the 'data' section of
        the config file (e.g., 'raw_data').
    filepath : str, optional
        A path string. If provided (not empty), this value is returned
        directly without reading the config file. Default is "".

    Returns
    -------
    str
        The resolved absolute file path.
    """
    configs_path = get_configs_path()

    if filepath == "":
        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config["data"][key]

            if not os.path.isabs(filepath):
                configs_dir = os.path.dirname(configs_path)
                filepath = os.path.join(configs_dir, filepath)

    return filepath
