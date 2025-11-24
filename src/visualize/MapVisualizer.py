"""
Geospatial visualization utilities using Folium and GeoPandas.

This module provides the MapVisualizer class, designed to generate interactive
choropleth maps that visualize data aggregated spatially to administrative
regions (subdistricts). It handles loading geographic boundaries and performing
spatial joins to aggregate point data before plotting.

Classes
-------
MapVisualizer
    A class for preparing point and polygon geospatial data and generating
    an interactive Folium map (via GeoPandas explore method).
"""

# Import necessary modules
import geopandas as gpd
import pandas as pd
from folium import Map
from shapely import wkt

# Utility Functions
from src.utils.ConfigUtils import read_config_path


class MapVisualizer:
    """
    Generates an interactive choropleth map by spatially joining point data
    to administrative regions and aggregating values.

    The visualizer loads both a DataFrame of geo-referenced points (expected
    to have coordinates and an 'type_cleaned' column) and a GeoDataFrame
    of administrative boundaries (subdistricts).

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame containing point data (coordinates, and 'type_cleaned').
    region_path : str, optional
        File path to the processed geographic boundary CSV file (which contains
        WKT geometry column). If provided, overrides the config path. Default is "".
    latitude_column : str, optional
        Name of the column containing latitude values. Defaults to "latitude".
    longitude_column : str, optional
        Name of the column containing longitude values. Defaults to "longitude".

    Attributes
    ----------
    df : pandas.DataFrame
        A copy of the input DataFrame.
    region_path : str
        The resolved absolute path to the geographic boundary CSV file.
    latitude_column : str
        The final column name used for latitude values.
    longitude_column : str
        The final column name used for longitude values.
    gdf_points : geopandas.GeoDataFrame
        GeoDataFrame of the input points, derived by exploding 'type_cleaned'.
    gdf_region : geopandas.GeoDataFrame
        GeoDataFrame of the administrative boundaries (subdistricts) loaded from CSV.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        region_path: str = "",
        latitude_column: str = "",
        longitude_column: str = "",
    ) -> None:
        """
        Initializes the visualizer and loads/processes the point and region geometries.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing point data.
        region_path : str, optional
            File path to the processed geographic boundary CSV file. Default is "".
        latitude_column : str, optional
            Name of the column containing latitude values. Defaults to "latitude".
        longitude_column : str, optional
            Name of the column containing longitude values. Defaults to "longitude".
        """

        self.df = df
        self.region_path = read_config_path(
            key="geographic_cleansed_data_path", filepath=region_path
        )
        self.latitude_column = latitude_column or "latitude"
        self.longitude_column = longitude_column or "longitude"

        self._load_geometries()

    def _load_geometries(self) -> None:
        """
        Processes and converts the raw DataFrame into two essential GeoDataFrames:
        `self.gdf_points` (point data with exploded categories) and
        `self.gdf_region` (polygons/regions from the CSV file).

        The region geometry is loaded from a CSV file where the geometry is stored
        in Well-Known Text (WKT) format.

        Returns
        -------
        None
            The method sets the `self.gdf_points` and `self.gdf_region` attributes.
        """

        df_type = self.df.copy()

        df_exploded = df_type.explode("type_cleaned")
        df_exploded["type_cleaned"] = df_exploded["type_cleaned"].str.strip()

        self.gdf_points = gpd.GeoDataFrame(
            df_exploded,
            geometry=gpd.points_from_xy(
                df_exploded[self.longitude_column], df_exploded[self.latitude_column]
            ),
            crs="EPSG:4326",
        )

        df_region = pd.read_csv(self.region_path)
        df_region["geometry"] = df_region["geometry"].map(wkt.loads)

        self.gdf_region = gpd.GeoDataFrame(
            df_region, geometry="geometry", crs="EPSG:4326"
        )

        return None

    def plot(self, type_filter: str | None = None, value_column: str = "count") -> Map:
        """
        Generates an interactive Folium choropleth map showing aggregated data.

        The method performs a spatial join between filtered points and regions,
        aggregates the data (count or mean of a value column), merges it with
        the region geometry, and plots the result using GeoPandas' `explore`
        method (which uses Folium).

        Parameters
        ----------
        type_filter : str or None, optional
            A specific value in the 'type_cleaned' column to filter the points by.
            If None, all points are included in the aggregation. Default is None.
        value_column : str, optional
            The column name to aggregate (calculate mean of) within each region.
            If set to 'count', the simple count of points is used. Default is "count".

        Returns
        -------
        folium.Map
            The generated interactive map object.
        """

        if type_filter:
            gdf_filtered = self.gdf_points[
                self.gdf_points["type_cleaned"] == type_filter
            ]
        else:
            gdf_filtered = self.gdf_points

        joined = gpd.sjoin(
            gdf_filtered, self.gdf_region, how="left", predicate="within"
        )

        if value_column == "count":
            agg_df = joined.groupby("subdistrict_name").size().reset_index(name="count")
        else:
            agg_df = (
                joined.groupby("subdistrict_name")[value_column]
                .mean()
                .reset_index(name="count")
            )

        gdf_merged = self.gdf_region.merge(agg_df, on="subdistrict_name", how="left")
        gdf_merged["count"] = gdf_merged["count"].fillna(0)

        gdf_proj = gdf_merged.to_crs(epsg=3857)
        union_geom = gdf_proj.geometry.unary_union
        center_proj = union_geom.centroid
        center_latlon = (
            gpd.GeoSeries([center_proj], crs=gdf_proj.crs).to_crs(epsg=4326).geometry[0]
        )

        minx, miny, maxx, maxy = gdf_merged.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]

        m = gdf_merged.explore(
            column="count",
            cmap="Oranges",
            legend=True,
            location=[center_latlon.coords[0][1], center_latlon.coords[0][0]],
            zoom_start=11,
            min_zoom=11,
            max_zoom=14,
            max_bounds=True,
            max_bounds_viscosity=1.0,
            map_kwds={"bounds": bounds},
        )

        m.options["zoomControl"] = False
        m.options["scrollWheelZoom"] = False
        m.options["doubleClickZoom"] = False
        m.options["touchZoom"] = False
        m.options["dragging"] = False

        return m
