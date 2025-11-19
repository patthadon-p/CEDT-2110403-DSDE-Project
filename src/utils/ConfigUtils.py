import os

import yaml


def read_config_path(configs_path: str, key: str, filepath: str) -> str:

    if filepath == "":

        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config["data"][key]

            if not os.path.isabs(filepath):
                configs_dir = os.path.dirname(configs_path)
                filepath = os.path.join(configs_dir, filepath)

    return filepath
