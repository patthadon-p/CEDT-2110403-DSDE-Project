# Import necessary modules
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Import utility functions
from .ConfigUtils import read_config_path


def load_geographic_data(filepath: str = "") -> gpd.GeoDataFrame:
    """
    Description:
    Load a GIS shapefile containing geographic data for Bangkok.

    Args:
        filepath (str): Path to the SHP file. If empty, defaults to the path specified in the configuration file.
    """

    filepath = read_config_path(key="bangkok_geographic_data_path", filepath=filepath)

    bangkok_geodata = gpd.read_file(filepath, encoding="utf-8").to_crs(epsg=4326)

    return bangkok_geodata


def save_geographic_data(
    df: gpd.GeoDataFrame | pd.DataFrame,
    filepath: str = "",
    save_name: str = "",
    drop_columns=None,
) -> None:
    """
    Description:
    Save the cleansed geographic data to a CSV file after renaming columns and dropping unnecessary ones.

    Args:
        df (gpd.GeoDataFrame | pd.DataFrame): The geographic data to be saved.
        filepath (str, optional): Path to the configuration file for geographic columns. Defaults to "".
        save_name (str, optional): Name of the file to save the cleansed data. Defaults to "".
        drop_columns (list, optional): List of columns to drop from the data. Defaults to None.

    Returns:
        None
    """
    filepath = read_config_path(key="geographic_columns_path", filepath=filepath)

    with open(filepath, encoding="utf-8") as file:
        rename_dict = json.load(file)

    df = df.rename(columns=rename_dict)
    df = df.drop(columns=drop_columns or "DROP")

    df["province_name"] = "กรุงเทพมหานคร"

    save_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / (save_name or "cleansed_geo.csv")
    )
    df.to_csv(save_path, index=False)

    return None
