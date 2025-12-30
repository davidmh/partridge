# flake8: noqa E501

import networkx as nx
import polars as pl

from .parsers import vparse_date, vparse_time


def to_numeric(s: pl.Series) -> pl.Series:
    return s.cast(pl.Float64, strict=False)


def to_int(s: pl.Series) -> pl.Series:
    return s.cast(pl.Int64, strict=False)


def empty_config() -> nx.DiGraph:
    return nx.DiGraph()


def default_config() -> nx.DiGraph:
    G = empty_config()
    add_edge_config(G)
    add_node_config(G)
    return G


def geo_config() -> nx.DiGraph:
    G = default_config()
    add_geo_config(G)
    return G


def add_edge_config(g: nx.DiGraph) -> nx.DiGraph:
    g.add_edges_from(
        [
            (
                "agency.txt",
                "routes.txt",
                {
                    "dependencies": [
                        {"agency.txt": "agency_id", "routes.txt": "agency_id"}
                    ]
                },
            ),
            (
                "calendar.txt",
                "trips.txt",
                {
                    "dependencies": [
                        {"calendar.txt": "service_id", "trips.txt": "service_id"}
                    ]
                },
            ),
            (
                "calendar_dates.txt",
                "trips.txt",
                {
                    "dependencies": [
                        {"calendar_dates.txt": "service_id", "trips.txt": "service_id"}
                    ]
                },
            ),
            (
                "fare_attributes.txt",
                "fare_rules.txt",
                {
                    "dependencies": [
                        {"fare_attributes.txt": "fare_id", "fare_rules.txt": "fare_id"}
                    ]
                },
            ),
            (
                "fare_rules.txt",
                "stops.txt",
                {
                    "dependencies": [
                        {"fare_rules.txt": "origin_id", "stops.txt": "zone_id"},
                        {"fare_rules.txt": "destination_id", "stops.txt": "zone_id"},
                        {"fare_rules.txt": "contains_id", "stops.txt": "zone_id"},
                    ]
                },
            ),
            (
                "fare_rules.txt",
                "routes.txt",
                {
                    "dependencies": [
                        {"fare_rules.txt": "route_id", "routes.txt": "route_id"}
                    ]
                },
            ),
            (
                "frequencies.txt",
                "trips.txt",
                {
                    "dependencies": [
                        {"frequencies.txt": "trip_id", "trips.txt": "trip_id"}
                    ]
                },
            ),
            (
                "routes.txt",
                "trips.txt",
                {"dependencies": [{"routes.txt": "route_id", "trips.txt": "route_id"}]},
            ),
            (
                "shapes.txt",
                "trips.txt",
                {"dependencies": [{"shapes.txt": "shape_id", "trips.txt": "shape_id"}]},
            ),
            (
                "stops.txt",
                "stop_times.txt",
                {
                    "dependencies": [
                        {"stops.txt": "stop_id", "stop_times.txt": "stop_id"}
                    ]
                },
            ),
            (
                "stop_times.txt",
                "trips.txt",
                {
                    "dependencies": [
                        {"stop_times.txt": "trip_id", "trips.txt": "trip_id"}
                    ]
                },
            ),
            (
                "transfers.txt",
                "stops.txt",
                {
                    "dependencies": [
                        {"transfers.txt": "from_stop_id", "stops.txt": "stop_id"},
                        {"transfers.txt": "to_stop_id", "stops.txt": "stop_id"},
                    ]
                },
            ),
        ]
    )


def add_node_config(g: nx.DiGraph) -> nx.DiGraph:
    g.add_nodes_from(
        [
            (
                "agency.txt",
                {"required_columns": ("agency_name", "agency_url", "agency_timezone")},
            ),
            (
                "calendar.txt",
                {
                    "converters": {
                        "start_date": vparse_date,
                        "end_date": vparse_date,
                        "monday": to_numeric,
                        "tuesday": to_numeric,
                        "wednesday": to_numeric,
                        "thursday": to_numeric,
                        "friday": to_numeric,
                        "saturday": to_numeric,
                        "sunday": to_numeric,
                    },
                    "required_columns": (
                        "service_id",
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                        "start_date",
                        "end_date",
                    ),
                },
            ),
            (
                "calendar_dates.txt",
                {
                    "converters": {
                        "date": vparse_date,
                        "exception_type": to_numeric,
                    },
                    "required_columns": ("service_id", "date", "exception_type"),
                },
            ),
            (
                "fare_attributes.txt",
                {
                    "converters": {
                        "price": to_numeric,
                        "payment_method": to_numeric,
                        "transfer_duration": to_numeric,
                    },
                    "required_columns": (
                        "fare_id",
                        "price",
                        "currency_type",
                        "payment_method",
                        "transfers",
                    ),
                },
            ),
            ("fare_rules.txt", {"required_columns": ("fare_id",)}),
            (
                "feed_info.txt",
                {
                    "converters": {
                        "feed_start_date": vparse_date,
                        "feed_end_date": vparse_date,
                    },
                    "required_columns": (
                        "feed_publisher_name",
                        "feed_publisher_url",
                        "feed_lang",
                    ),
                },
            ),
            (
                "frequencies.txt",
                {
                    "converters": {
                        "headway_secs": to_numeric,
                        "exact_times": to_numeric,
                        "start_time": vparse_time,
                        "end_time": vparse_time,
                    },
                    "required_columns": (
                        "trip_id",
                        "start_time",
                        "end_time",
                        "headway_secs",
                    ),
                },
            ),
            (
                "routes.txt",
                {
                    "converters": {"route_type": to_numeric},
                    "required_columns": (
                        "route_id",
                        "route_short_name",
                        "route_long_name",
                        "route_type",
                    ),
                },
            ),
            (
                "shapes.txt",
                {
                    "converters": {
                        "shape_pt_lat": to_numeric,
                        "shape_pt_lon": to_numeric,
                        "shape_pt_sequence": to_numeric,
                        "shape_dist_traveled": to_numeric,
                    },
                    "required_columns": (
                        "shape_id",
                        "shape_pt_lat",
                        "shape_pt_lon",
                        "shape_pt_sequence",
                    ),
                },
            ),
            (
                "stops.txt",
                {
                    "converters": {
                        "stop_lat": to_numeric,
                        "stop_lon": to_numeric,
                        "location_type": to_numeric,
                        "wheelchair_boarding": to_numeric,
                        "pickup_type": to_numeric,
                        "drop_off_type": to_numeric,
                        "shape_dist_traveled": to_numeric,
                        "timepoint": to_numeric,
                    },
                    "required_columns": (
                        "stop_id",
                        "stop_name",
                        "stop_lat",
                        "stop_lon",
                    ),
                },
            ),
            (
                "stop_times.txt",
                {
                    "converters": {
                        "arrival_time": vparse_time,
                        "departure_time": vparse_time,
                        "pickup_type": to_numeric,
                        "shape_dist_traveled": to_numeric,
                        "stop_sequence": to_int,
                        "timepoint": to_numeric,
                    },
                    "required_columns": (
                        "trip_id",
                        "arrival_time",
                        "departure_time",
                        "stop_id",
                        "stop_sequence",
                    ),
                },
            ),
            (
                "transfers.txt",
                {
                    "converters": {
                        "transfer_type": to_numeric,
                        "min_transfer_time": to_numeric,
                    },
                    "required_columns": ("from_stop_id", "to_stop_id", "transfer_type"),
                },
            ),
            (
                "trips.txt",
                {
                    "converters": {
                        "direction_id": to_numeric,
                        "wheelchair_accessible": to_numeric,
                        "bikes_allowed": to_numeric,
                    },
                    "required_columns": ("route_id", "service_id", "trip_id"),
                },
            ),
        ]
    )


def add_geo_config(g: nx.DiGraph) -> nx.DiGraph:
    from .geo import build_shapes, build_stops

    for node, transform in (("shapes.txt", build_shapes), ("stops.txt", build_stops)):
        assert node in g.nodes, "Missing config for node: {}".format(node)

        if "transformations" not in g.nodes[node]:
            g.nodes[node]["transformations"] = []

        g.nodes[node]["transformations"].append(transform)

    return g


def reroot_graph(G: nx.DiGraph, node: str) -> nx.DiGraph:
    """Return a copy of the graph rooted at the given node"""
    G = G.copy()
    for n, successors in list(nx.bfs_successors(G, source=node)):
        for s in successors:
            G.add_edge(s, n, **G.edges[n, s])
            G.remove_edge(n, s)
    return G
