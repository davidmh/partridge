import os
import tempfile

import partridge as ptg
import pytest
import polars as pl

from .helpers import fixture, zip_file


@pytest.mark.parametrize(
    "path", [zip_file("seattle-area-2017-11-16"), fixture("seattle-area-2017-11-16")]
)
def test_extract_agencies(path):
    fd = ptg.load_feed(path)

    agencies = fd.agency
    assert len(agencies) == 3

    routes = fd.routes
    assert len(routes) == 14

    agency_ids = [agencies["agency_id"][0]]
    route_ids = set(fd.routes.filter(pl.col("agency_id").is_in(agency_ids))["route_id"])
    trip_ids = set(fd.trips.filter(pl.col("route_id").is_in(route_ids))["trip_id"])
    stop_ids = set(fd.stop_times.filter(pl.col("trip_id").is_in(trip_ids))["stop_id"])

    assert len(route_ids)
    assert len(trip_ids)
    assert len(stop_ids)

    with tempfile.TemporaryDirectory() as tmpdir:
        outfile = os.path.join(tmpdir, "test.zip")

        result = ptg.extract_feed(
            path, outfile, {"routes.txt": {"agency_id": agency_ids}}
        )
        assert result == outfile

        new_fd = ptg.load_feed(outfile)
        assert list(new_fd.agency["agency_id"]) == agency_ids
        assert set(new_fd.routes["route_id"]) == route_ids
        assert set(new_fd.trips["trip_id"]) == trip_ids
        assert set(new_fd.stop_times["trip_id"]) == trip_ids
        assert set(new_fd.stops["stop_id"]) == stop_ids

        nodes = []
        for node in fd._config.nodes():
            df = fd.get(node)
            if not df.is_empty():
                nodes.append(node)

        assert len(nodes)

        for node in nodes:
            original_df = fd.get(node)
            new_df = new_fd.get(node)
            assert set(original_df.columns) == set(new_df.columns)


@pytest.mark.parametrize(
    "path", [zip_file("seattle-area-2017-11-16"), fixture("seattle-area-2017-11-16")]
)
def test_extract_routes(path):
    fd = ptg.load_feed(path)

    agencies = fd.agency
    assert len(agencies) == 3

    routes = fd.routes
    assert len(routes) == 14

    route_ids = [routes["route_id"][0]]
    agency_ids = set(fd.routes.filter(pl.col("route_id").is_in(route_ids))["agency_id"])
    trip_ids = set(fd.trips.filter(pl.col("route_id").is_in(route_ids))["trip_id"])
    stop_ids = set(fd.stop_times.filter(pl.col("trip_id").is_in(trip_ids))["stop_id"])

    assert len(agency_ids)
    assert len(trip_ids)
    assert len(stop_ids)

    with tempfile.TemporaryDirectory() as tmpdir:
        outfile = os.path.join(tmpdir, "test.zip")

        result = ptg.extract_feed(path, outfile, {"trips.txt": {"route_id": route_ids}})
        assert result == outfile

        new_fd = ptg.load_feed(outfile)
        assert list(new_fd.routes["route_id"]) == route_ids
        assert set(new_fd.agency["agency_id"]) == agency_ids
        assert set(new_fd.trips["trip_id"]) == trip_ids
        assert set(new_fd.stop_times["trip_id"]) == trip_ids
        assert set(new_fd.stops["stop_id"]) == stop_ids

        nodes = []
        for node in fd._config.nodes():
            df = fd.get(node)
            if not df.is_empty():
                nodes.append(node)

        assert len(nodes)

        for node in nodes:
            original_df = fd.get(node)
            new_df = new_fd.get(node)
            assert set(original_df.columns) == set(new_df.columns)
