import json
import os

import yaml

# Get the absolute path to the configs directory
configs_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs",
    "configs.yaml",
)


def load_province_whitelist(filepath: str = "") -> dict:
    """
    Description:
    Load a JSON file containing a whitelist of valid province names.

    Args:
        filepath (str): Path to the JSON file. If empty, defaults to the path specified in the configuration file.
    """
    if filepath == "":
        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config["data"]["province_whitelist_path"]

        # If the filepath is relative, make it relative to the configs directory
        if not os.path.isabs(filepath):
            configs_dir = os.path.dirname(configs_path)
            filepath = os.path.join(configs_dir, filepath)

    # Debug: print the resolved filepath (remove this line in production)
    print(f"Loading province whitelist from: {filepath}")

    with open(filepath, encoding="utf-8") as file:
        provinces = json.load(file)

    whitelist = {}
    for standard_name, variants in provinces.items():
        for name in variants:
            whitelist[name] = standard_name

    return whitelist
