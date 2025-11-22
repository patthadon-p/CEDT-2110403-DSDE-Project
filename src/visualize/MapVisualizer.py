# Import necessary modules
import geopandas as gpd
import pandas as pd
from folium import Map
from shapely import wkt

# Utility Functions
from src.utils.ConfigUtils import read_config_path


class MapVisualizer:
    def __init__(
        self,
        df: pd.DataFrame,
        region_path: str = "",
        latitude_column: str = "",
        longitude_column: str = "",
    ) -> None:
        self.df = df
        self.region_path = read_config_path(
            key="geographic_cleansed_data_path", filepath=region_path
        )
        self.latitude_column = latitude_column or "latitude"
        self.longitude_column = longitude_column or "longitude"

        self._load_geometries()

    def _load_geometries(self) -> None:
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
