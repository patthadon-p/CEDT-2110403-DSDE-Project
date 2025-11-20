# Import necessary modules
import os
from pathlib import Path

import yaml


# Define the path to the configs directory
def get_configs_path() -> str:
    """Get the absolute path to the configs.yaml file."""
    base_dir = Path(__file__).resolve().parents[2]
    configs_path = base_dir / "configs" / "configs.yaml"
    return str(configs_path)


def read_config_path(key: str, domain: str = "data", filepath: str = "") -> str:
    """Read a file path from the config file and resolve it to an absolute path."""
    configs_path = get_configs_path()

    if filepath == "":
        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config[domain][key]

            if not os.path.isabs(filepath):
                configs_dir = os.path.dirname(configs_path)
                filepath = os.path.join(configs_dir, filepath)

    return filepath
