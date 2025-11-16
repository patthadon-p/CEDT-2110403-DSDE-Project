import os

import geopandas as gpd
import yaml

# Get the absolute path to the configs directory
configs_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs",
    "configs.yaml",
)


def load_geographic_data(filepath: str = "") -> gpd.GeoDataFrame:
    """
    Description:
    Load a GIS shapefile containing geographic data for Bangkok.

    Args:
        filepath (str): Path to the SHP file. If empty, defaults to the path specified in the configuration file.
    """
    if filepath == "":
        with open(configs_path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            filepath = config["data"]["bangkok_geographic_data_path"]

        # If the filepath is relative, make it relative to the configs directory
        if not os.path.isabs(filepath):
            configs_dir = os.path.dirname(configs_path)
            filepath = os.path.join(configs_dir, filepath)

    bangkok_geodata = gpd.read_file(filepath, encoding="utf-8").to_crs(epsg=4326)

    return bangkok_geodata
