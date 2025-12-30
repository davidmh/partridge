import polars as pl

try:
    # GeoPolars is still a prototype, it doesn't have types yet.
    import geopolars as gpl  # type: ignore
    from shapely.geometry import LineString, Point
except ImportError as impexc:
    print(impexc)
    print("You must install GeoPolars to use this module.")
    raise


DEFAULT_CRS = "EPSG:4326"


def build_shapes(df: pl.DataFrame) -> pl.DataFrame:
    """
    Build a GeoDataFrame of shapes from a Polars DataFrame.
    Returns a Polars DataFrame with a geometry column handled by GeoPolars.
    """
    if df.is_empty():
        return pl.DataFrame(
            {"shape_id": [], "geometry": []},
            schema={"shape_id": pl.Utf8, "geometry": pl.Object},
        )

    # Sort by shape_pt_sequence to ensure correct line construction
    df_sorted = df.sort("shape_pt_sequence")

    # Group by shape_id and aggregate points into LineString
    # Note: GeoPolars is still experimental. We'll construct WKT or Shapely objects first
    # then convert if needed, or stick to Polars with object column for geometry for now
    # similar to how GeoPandas works but with Polars backend.

    # Aggregate lon/lats into lists, then map to LineString
    # We use python list comprehension to avoid map_elements overhead
    aggregated = df_sorted.group_by("shape_id", maintain_order=True).agg(
        [pl.col("shape_pt_lon"), pl.col("shape_pt_lat")]
    )

    shape_ids = aggregated["shape_id"]
    lons = aggregated["shape_pt_lon"].to_list()
    lats = aggregated["shape_pt_lat"].to_list()

    geometry = [LineString(zip(lon, lat)) for lon, lat in zip(lons, lats)]

    shapes = pl.DataFrame(
        {"shape_id": shape_ids, "geometry": geometry},
        schema={"shape_id": pl.Utf8, "geometry": pl.Object},
    )

    # Convert to GeoPolars DataFrame (which is just a Polars DF with geo metadata)
    # Currently GeoPolars is an extension.
    # For now, we return a standard Polars DataFrame containing shapely objects,
    # which is the closest equivalent until `geopolars.from_polars` is fully robust.
    # Note: `geopolars` 0.1.0a4 does not have `from_polars` exposed at top level yet,
    # but `GeoDataFrame` constructor can take a polars DataFrame.
    return gpl.GeoDataFrame(shapes)  # type: ignore


def build_stops(df: pl.DataFrame) -> pl.DataFrame:
    """
    Build a GeoDataFrame of stops from a Polars DataFrame.
    """
    if df.is_empty():
        # Create empty DataFrame with correct columns
        schema = {c: df.schema[c] for c in df.columns}
        schema["geometry"] = pl.Object  # type: ignore
        return pl.DataFrame(schema=schema)

    # Create points using list comprehension to avoid map_elements overhead
    lons = df["stop_lon"].to_list()
    lats = df["stop_lat"].to_list()
    geometry = [Point(x, y) for x, y in zip(lons, lats)]

    stops = df.drop(["stop_lon", "stop_lat"]).with_columns(
        pl.Series("geometry", geometry, dtype=pl.Object)
    )

    return gpl.GeoDataFrame(stops)  # type: ignore
