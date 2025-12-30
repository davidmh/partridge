import os
from threading import RLock
from typing import Dict, Optional, Union

import networkx as nx
import polars as pl

from .config import default_config
from .types import View
from .utilities import detect_encoding, empty_df, setwrap


def _read_file(filename: str) -> property:
    def getter(self) -> pl.DataFrame:
        return self.get(filename)

    return property(getter)


class Feed(object):
    def __init__(
        self,
        source: Union[str, "Feed"],
        view: Optional[View] = None,
        config: Optional[nx.DiGraph] = None,
    ):
        self._config: nx.DiGraph = default_config() if config is None else config
        self._view: View = {} if view is None else view
        self._cache: Dict[str, pl.DataFrame] = {}
        self._pathmap: Dict[str, str] = {}
        self._delete_after_reading: bool = False
        self._shared_lock = RLock()
        self._locks: Dict[str, RLock] = {}
        if isinstance(source, self.__class__):
            self._read = source.get
        elif isinstance(source, str) and os.path.isdir(source):
            self._read = self._read_csv
            self._bootstrap(source)
        else:
            raise ValueError("Invalid source")

    def get(self, filename: str) -> pl.DataFrame:
        lock = self._locks.get(filename, self._shared_lock)
        with lock:
            df = self._cache.get(filename)
            if df is None:
                df = self._read(filename)
                df = self._filter(filename, df)
                df = self._prune(filename, df)
                df = self._convert_types(filename, df)
                df = self._transform(filename, df)
                self.set(filename, df)
            return self._cache[filename]

    def set(self, filename: str, df: pl.DataFrame) -> None:
        lock = self._locks.get(filename, self._shared_lock)
        with lock:
            self._cache[filename] = df

    agency = _read_file("agency.txt")
    calendar = _read_file("calendar.txt")
    calendar_dates = _read_file("calendar_dates.txt")
    fare_attributes = _read_file("fare_attributes.txt")
    fare_rules = _read_file("fare_rules.txt")
    feed_info = _read_file("feed_info.txt")
    frequencies = _read_file("frequencies.txt")
    routes = _read_file("routes.txt")
    shapes = _read_file("shapes.txt")
    stops = _read_file("stops.txt")
    stop_times = _read_file("stop_times.txt")
    transfers = _read_file("transfers.txt")
    trips = _read_file("trips.txt")

    def _bootstrap(self, path: str) -> None:
        # Walk recursively through the directory
        for root, _subdirs, files in os.walk(path):
            for fname in files:
                basename = os.path.basename(fname)
                if basename in self._pathmap:
                    # Verify that the folder does not contain multiple files of the same name.
                    raise ValueError("More than one {} in folder".format(basename))
                # Index paths by their basename.
                self._pathmap[basename] = os.path.join(root, fname)
                # Build a lock for each file to synchronize reads.
                self._locks[basename] = RLock()

    def _read_csv(self, filename: str) -> pl.DataFrame:
        path = self._pathmap.get(filename)
        columns = self._config.nodes.get(filename, {}).get("required_columns", [])

        if path is None or os.path.getsize(path) == 0:
            # The file is missing or empty. Return an empty
            # DataFrame containing any required columns.
            return empty_df(columns)

        # If the file isn't in the zip, return an empty DataFrame.
        with open(path, "rb") as f:
            encoding = detect_encoding(f)

        try:
            df = pl.read_csv(
                path,
                infer_schema_length=0,
                encoding=encoding,
                ignore_errors=True,
            )
        except pl.exceptions.ComputeError:
            return empty_df(columns)

        # Strip leading/trailing whitespace from column names
        df = df.rename({col: col.strip() for col in df.columns})

        if not df.is_empty():
            # Strip leading/trailing whitespace from column values
            df = df.select([pl.col(col).str.strip_chars() for col in df.columns])

        return df

    def _filter(self, filename: str, df: pl.DataFrame) -> pl.DataFrame:
        """Apply view filters"""
        view = self._view.get(filename)
        if view is None:
            return df

        for col, values in view.items():
            # If applicable, filter this dataframe by the given set of values
            if col in df.columns:
                df = df.filter(pl.col(col).is_in(setwrap(values)))

        return df

    def _prune(self, filename: str, df: pl.DataFrame) -> pl.DataFrame:
        """Depth-first search through the dependency graph
        and prune dependent DataFrames along the way.
        """
        dependencies = []
        for _, depf, data in self._config.out_edges(filename, data=True):
            deps = data.get("dependencies")
            if deps is None:
                msg = f"Edge missing `dependencies` attribute: {filename}->{depf}"
                raise ValueError(msg)
            dependencies.append((depf, deps))

        if not dependencies:
            return df

        for depfile, column_pairs in dependencies:
            # Read the filtered, cached file dependency
            depdf = self.get(depfile)
            for deps in column_pairs:
                col = deps[filename]
                depcol = deps[depfile]
                # If applicable, prune this dataframe by the other
                if col in df.columns and depcol in depdf.columns:
                    df = df.filter(pl.col(col).is_in(depdf[depcol]))

        return df

    def _convert_types(self, filename: str, df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply type conversions
        """
        if df.is_empty():
            return df

        converters = self._config.nodes.get(filename, {}).get("converters", {})

        # Apply converters
        cols_to_convert = []
        for col, converter in converters.items():
            if col in df.columns:
                cols_to_convert.append(converter(df[col]).alias(col))

        if cols_to_convert:
            df = df.with_columns(cols_to_convert)

        return df

    def _transform(self, filename: str, df: pl.DataFrame) -> pl.DataFrame:
        transformations = self._config.nodes.get(filename, {}).get(
            "transformations", []
        )

        for transform in transformations:
            df = transform(df)

        return df

    # Adding explicit property access for compatibility
    @property
    def stops(self):
        return self.get("stops.txt")

    @property
    def stop_times(self):
        return self.get("stop_times.txt")

    @property
    def trips(self):
        return self.get("trips.txt")

    @property
    def routes(self):
        return self.get("routes.txt")

    @property
    def agency(self):
        return self.get("agency.txt")

    @property
    def calendar(self):
        return self.get("calendar.txt")

    @property
    def calendar_dates(self):
        return self.get("calendar_dates.txt")

    @property
    def fare_attributes(self):
        return self.get("fare_attributes.txt")

    @property
    def fare_rules(self):
        return self.get("fare_rules.txt")

    @property
    def feed_info(self):
        return self.get("feed_info.txt")

    @property
    def frequencies(self):
        return self.get("frequencies.txt")

    @property
    def shapes(self):
        return self.get("shapes.txt")

    @property
    def transfers(self):
        return self.get("transfers.txt")
