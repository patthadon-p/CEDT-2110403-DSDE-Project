import os

import pandas as pd
import geopandas as gpd
from shapely import wkt

def MapVisualizer(df, longitude_column="longitude", latitude_column="latitude"):
  gdf_points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df[longitude_column], df[latitude_column]),
    crs="EPSG:4326"
  )

  df_region = pd.read_csv("../data/processed/cleansed_geo.csv")
  df_region['geometry'] = df_region['geometry'].apply(wkt.loads)
  gdf_region = gpd.GeoDataFrame(df_region, geometry='geometry', crs="EPSG:4326")

  joined = gpd.sjoin(gdf_points, gdf_region, how="left", predicate="within")

  counts = joined.groupby("subdistrict_name").size().reset_index(name="count")

  gdf_merged = gdf_region.merge(counts, on="subdistrict_name", how="left")
  gdf_merged["count"] = gdf_merged["count"].fillna(0)

  gdf_proj = gdf_merged.to_crs(epsg=3857)

  union_geom = gdf_proj.geometry.union_all()

  center_proj = union_geom.centroid

  center_latlon = gpd.GeoSeries([center_proj], crs=gdf_proj.crs).to_crs(epsg=4326).geometry[0]

  minx, miny, maxx, maxy = gdf_merged.total_bounds

  bounds = [[miny, minx], [maxy, maxx]]

  print(bounds)

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
    map_kwds={
        "bounds": bounds
    }
  )

  # --- Disable all zoom interactions ---
  m.options["zoomControl"] = False           # removes + / − buttons
  # m.options["scrollWheelZoom"] = False       # block zoom with mouse wheel
  m.options["doubleClickZoom"] = False       # block double-click zoom
  # m.options["touchZoom"] = False             # block touch zoom (mobile)
  # m.options["dragging"] = False              # keep dragging so you can move the map

  return m


# # Usage Example:

# from src.visualize.MapVisualizer import MapVisualizer
# m = MapVisualizer(df_cleansed, longitude_column="longitude", latitude_column="latitude")
# m.save("../data/visualize/map.html")