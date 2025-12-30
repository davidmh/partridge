from typing import Dict, List

import polars as pl

try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point
except ImportError as impexc:
    print(impexc)
    print("You must install GeoPandas to use this module.")
    raise


DEFAULT_CRS = {"init": "EPSG:4326"}


def build_shapes(df: pl.DataFrame) -> gpd.GeoDataFrame:
    if df.is_empty():
        return gpd.GeoDataFrame({"shape_id": [], "geometry": []}, crs=DEFAULT_CRS)

    data: Dict[str, List] = {"shape_id": [], "geometry": []}

    # Sort and group
    df_sorted = df.sort("shape_pt_sequence")

    # Efficiently group by shape_id and collect coordinates
    for shape_id, shape_df in df_sorted.group_by("shape_id", maintain_order=True):
        shape_id_val = shape_id[0] if isinstance(shape_id, tuple) else shape_id
        data["shape_id"].append(shape_id_val)

        lons = shape_df["shape_pt_lon"].to_list()
        lats = shape_df["shape_pt_lat"].to_list()

        data["geometry"].append(LineString(list(zip(lons, lats))))

    return gpd.GeoDataFrame(data, crs=DEFAULT_CRS)


def build_stops(df: pl.DataFrame) -> gpd.GeoDataFrame:
    if df.is_empty():
        # Create empty GeoDataFrame with correct columns
        return gpd.GeoDataFrame(
            {c: [] for c in df.columns}, geometry=[], crs=DEFAULT_CRS
        )

    # Use list comprehension for better performance than apply
    lons = df["stop_lon"].to_list()
    lats = df["stop_lat"].to_list()
    geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]

    # Create GeoDataFrame directly from Polars dict to avoid pandas dependency
    data = df.drop(["stop_lon", "stop_lat"]).to_dict(as_series=False)
    data["geometry"] = geometry

    return gpd.GeoDataFrame(data, crs={"init": "EPSG:4326"})
