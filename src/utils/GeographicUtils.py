import geopandas as gpd

from src.utils.ConfigUtils import read_config_path

# Get the absolute path to the configs directory
from utils import configs_path


def load_geographic_data(filepath: str = "") -> gpd.GeoDataFrame:
    """
    Description:
    Load a GIS shapefile containing geographic data for Bangkok.

    Args:
        filepath (str): Path to the SHP file. If empty, defaults to the path specified in the configuration file.
    """

    filepath = read_config_path(
        configs_path, key="bangkok_geographic_data_path", filepath=filepath
    )

    bangkok_geodata = gpd.read_file(filepath, encoding="utf-8").to_crs(epsg=4326)

    return bangkok_geodata
