import pandas as pd
import geopandas as gpd
from shapely import wkt

class MapVisualizer:
    def __init__(self, df, region_path="../data/processed/cleansed_geo.csv"):
        """
        df : DataFrame containing latitude, longitude, and issue data
        region_path : CSV file containing subdistrict polygons (geometry in WKT)
        """
        self.df = df
        self.region_path = region_path

        self.latitude_column = "latitude"
        self.longitude_column = "longitude"

        self._load_geometries()

    def _load_geometries(self):
        """Convert df to GeoDataFrame and load Bangkok polygon shapefile."""

        df_type = self.df.copy()

        df_type["type_clean"] = (
            df_type["type"]
            .astype(str)
            .str.replace("{", "")
            .str.replace("}", "")
            .str.split(",")
        )
        df_exploded = df_type.explode("type_clean")
        df_exploded["type_clean"] = df_exploded["type_clean"].str.strip()

        self.gdf_points = gpd.GeoDataFrame(
            df_exploded,
            geometry=gpd.points_from_xy(
                df_exploded[self.longitude_column],
                df_exploded[self.latitude_column]
            ),
            crs="EPSG:4326"
        )

        df_region = pd.read_csv(self.region_path)
        df_region["geometry"] = df_region["geometry"].apply(wkt.loads)

        self.gdf_region = gpd.GeoDataFrame(
            df_region,
            geometry="geometry",
            crs="EPSG:4326"
        )

    def plot(self, type_filter=None, value_column="count"):
        """
        Generate an interactive heatmap of issue counts or a numeric column per subdistrict.
        """
        if type_filter:
            gdf_filtered = self.gdf_points[self.gdf_points["type_clean"] == type_filter]
        else:
            gdf_filtered = self.gdf_points

        joined = gpd.sjoin(
            gdf_filtered,
            self.gdf_region,
            how="left",
            predicate="within"
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
            gpd.GeoSeries([center_proj], crs=gdf_proj.crs)
            .to_crs(epsg=4326)
            .geometry[0]
        )

        minx, miny, maxx, maxy = gdf_merged.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]

        m = gdf_merged.explore(
            column="count",
            cmap="Oranges",
            legend=True,
            tooltip=["subdistrict_name", "count"],
            popup=True,
            location=[center_latlon.y, center_latlon.x],
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


