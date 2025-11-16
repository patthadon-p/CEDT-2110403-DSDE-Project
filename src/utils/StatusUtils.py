import json
import os

import yaml

# Get the absolute path to the configs directory
configs_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs",
    "configs.yaml",
)


def load_status_mapping(filepath: str = "") -> dict:
    """
    Description:
    Load a JSON file containing the mapping of state values to status values.

    Args:
        filepath (str): Path to the JSON file. If empty, defaults to the path specified in the configuration file.
    """
    if filepath == "":
        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config["data"]["status_mapping_path"]

        # If the filepath is relative, make it relative to the configs directory
        if not os.path.isabs(filepath):
            configs_dir = os.path.dirname(configs_path)
            filepath = os.path.join(configs_dir, filepath)

    with open(filepath, encoding="utf-8") as file:
        status_mapping = json.load(file)

    return status_mapping
