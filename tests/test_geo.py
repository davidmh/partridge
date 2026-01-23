import polars as pl
import pytest

try:
    from shapely.geometry import LineString, Point
    import geopolars as gpl  # type: ignore
    from partridge.geo import build_shapes, build_stops
except ImportError:
    gpl = None


@pytest.mark.skipif(gpl is None, reason="GeoPolars not installed")
def test_build_shapes():
    # Create sample data for shapes
    df = pl.DataFrame(
        {
            "shape_id": ["s1", "s1", "s2", "s2"],
            "shape_pt_lon": [1.0, 2.0, 3.0, 4.0],
            "shape_pt_lat": [10.0, 20.0, 30.0, 40.0],
            "shape_pt_sequence": [1, 2, 1, 2],
        }
    )

    shapes = build_shapes(df)

    assert shapes.shape == (2, 2)
    assert "geometry" in shapes.columns
    assert "shape_id" in shapes.columns

    # Sort to ensure consistent order
    shapes = shapes.sort("shape_id")

    # Check first shape
    geom1 = shapes.filter(pl.col("shape_id") == "s1")["geometry"][0]
    assert isinstance(geom1, LineString)
    assert list(geom1.coords) == [(1.0, 10.0), (2.0, 20.0)]

    # Check second shape
    geom2 = shapes.filter(pl.col("shape_id") == "s2")["geometry"][0]
    assert isinstance(geom2, LineString)
    assert list(geom2.coords) == [(3.0, 30.0), (4.0, 40.0)]


@pytest.mark.skipif(gpl is None, reason="GeoPolars not installed")
def test_build_shapes_empty():
    df = pl.DataFrame(
        {
            "shape_id": [],
            "shape_pt_lon": [],
            "shape_pt_lat": [],
            "shape_pt_sequence": [],
        },
        schema={
            "shape_id": pl.Utf8,
            "shape_pt_lon": pl.Float64,
            "shape_pt_lat": pl.Float64,
            "shape_pt_sequence": pl.Int64,
        },
    )

    shapes = build_shapes(df)
    assert shapes.is_empty()
    assert "geometry" in shapes.columns


@pytest.mark.skipif(gpl is None, reason="GeoPolars not installed")
def test_build_stops():
    # Create sample data for stops
    df = pl.DataFrame(
        {
            "stop_id": ["st1", "st2"],
            "stop_lon": [1.0, 2.0],
            "stop_lat": [10.0, 20.0],
            "stop_name": ["Stop 1", "Stop 2"],
        }
    )

    stops = build_stops(df)

    assert stops.shape == (2, 3)  # stop_id, stop_name, geometry
    assert "geometry" in stops.columns
    assert "stop_lon" not in stops.columns
    assert "stop_lat" not in stops.columns

    # Check first stop
    geom1 = stops.filter(pl.col("stop_id") == "st1")["geometry"][0]
    assert isinstance(geom1, Point)
    assert list(geom1.coords) == [(1.0, 10.0)]


@pytest.mark.skipif(gpl is None, reason="GeoPolars not installed")
def test_build_stops_empty():
    df = pl.DataFrame(
        {"stop_id": [], "stop_lon": [], "stop_lat": [], "stop_name": []},
        schema={
            "stop_id": pl.Utf8,
            "stop_lon": pl.Float64,
            "stop_lat": pl.Float64,
            "stop_name": pl.Utf8,
        },
    )

    stops = build_stops(df)
    assert stops.is_empty()
    assert "geometry" in stops.columns
    assert "stop_id" in stops.columns
