"""
Utilities for loading and saving geographic data using GeoPandas.

This module provides specialized functions for reading spatial data files
(e.g., Shapefiles, GeoJSON) into GeoDataFrames, ensuring standard CRS
is applied, and saving processed data with standardized column names and
additional metadata.

Functions
---------
load_geographic_data
    Loads geographic data from a path configured in the YAML file
    and converts the CRS to EPSG:4326.
save_geographic_data
    Saves a GeoDataFrame or DataFrame after renaming columns, dropping
    unwanted fields, and adding the province name metadata.
"""

# Import necessary modules
import json

import geopandas as gpd
import pandas as pd

# Import utility functions
from .ConfigUtils import get_data_dir, read_config_path


def load_geographic_data(filepath: str = "") -> gpd.GeoDataFrame:
    """
    Loads geographic data for Bangkok and transforms its Coordinate Reference System (CRS).

    The file path is retrieved using the key 'bangkok_geographic_data_path'
    from the config utility. The loaded GeoDataFrame is automatically converted
    to the standard WGS 84 CRS (EPSG:4326).

    Parameters
    ----------
    filepath : str, optional
        The absolute path to the geographic data file (e.g., GeoJSON, Shapefile).
        If provided, this path overrides the path specified in the config file.
        Default is "".

    Returns
    -------
    geopandas.GeoDataFrame
        The loaded geographic data with its geometry column transformed
        to EPSG:4326 CRS.

    Raises
    ------
    FileNotFoundError
        If the resolved file path does not exist.

    See Also
    --------
    .ConfigUtils.read_config_path : The utility function used to resolve the path.
    """

    filepath = read_config_path(key="bangkok_geographic_data_path", filepath=filepath)

    bangkok_geodata = gpd.read_file(filepath, encoding="utf-8").to_crs(epsg=4326)

    return bangkok_geodata


def save_geographic_data(
    df: gpd.GeoDataFrame | pd.DataFrame,
    filepath: str = "",
    save_name: str = "",
    drop_columns: list[str] | None = None,
) -> None:
    """
    Standardizes, cleans, and saves the provided GeoDataFrame or DataFrame as a CSV file.

    The function performs the following steps:
    1. Loads a column renaming map from a configured JSON file.
    2. Renames columns in the input DataFrame.
    3. Drops specified columns (defaults to dropping "DROP" if no list is provided).
    4. Adds a 'province_name' column with the value 'กรุงเทพมหานคร'.
    5. Saves the final DataFrame to the project's 'data/processed' directory.

    Parameters
    ----------
    df : geopandas.GeoDataFrame or pandas.DataFrame
        The DataFrame or GeoDataFrame to be processed and saved.
    filepath : str, optional
        Path to the JSON file containing the column renaming dictionary.
        If provided, overrides the config path 'geographic_columns_path'.
        Default is "".
    save_name : str, optional
        **The filename/path for the output CSV.** If provided, this value overrides
        the path specified in the config file under 'geographic_cleansed_data_path'.
        Defaults to the value in the config file.
    drop_columns : list of str or None, optional
        A list of columns to be dropped from the DataFrame. The underlying
        code defaults to dropping the column named "DROP" if this parameter
        is passed as None or empty.

    Returns
    -------
    None
        The function does not return a value.

    See Also
    --------
    .ConfigUtils.read_config_path : The utility function used to resolve the path.

    Notes
    -----
    The output file is saved to: project_root/data/processed/{save_name}.
    """

    filepath = read_config_path(key="geographic_columns_path", filepath=filepath)
    save_name = read_config_path(
        key="geographic_cleansed_data_path", filepath=save_name
    )

    with open(filepath, encoding="utf-8") as file:
        rename_dict = json.load(file)

    df = df.rename(columns=rename_dict)
    df = df.drop(columns=drop_columns or "DROP")

    df["province_name"] = "กรุงเทพมหานคร"

    save_path = get_data_dir() / "processed" / save_name
    df.to_csv(save_path, index=False)

    return None
