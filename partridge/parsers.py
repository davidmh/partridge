import datetime
from functools import lru_cache
from typing import Optional, Union
import polars as pl
import math


DATE_FORMAT = "%Y%m%d"


# Why 2^17? See https://git.io/vxB2P.
@lru_cache(maxsize=2**17)
def parse_time(val: Optional[Union[str, float]]) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return float("nan")

    val = str(val).strip()

    if val == "":
        return float("nan")

    try:
        h, m, s = val.split(":")
        ssm = int(h) * 3600 + int(m) * 60 + int(s)
        return float(ssm)
    except (ValueError, AttributeError):
        raise ValueError("invalid literal for int()")


def parse_date(val: str) -> datetime.date:
    return datetime.datetime.strptime(val, DATE_FORMAT).date()


def vparse_time(s: pl.Series) -> pl.Series:
    if not isinstance(s, pl.Series):
        s = pl.Series(s)

    # If already numeric (Float64, Int64, etc.), return as Float64
    if s.dtype.is_numeric():
        return s.cast(pl.Float64)

    # Capture 3 groups: Hours, Minutes, Seconds.
    # The regex allows for leading/trailing whitespace.
    # It strictly matches h:m:s format.
    pattern = r"^\s*(-?\d+):(\d+):(\d+)\s*$"

    # extract_groups returns a Struct with fields "1", "2", "3"
    struct_s = s.str.extract_groups(pattern)

    h = struct_s.struct.field("1").cast(pl.Float64)
    m = struct_s.struct.field("2").cast(pl.Float64)
    sec = struct_s.struct.field("3").cast(pl.Float64)

    return h * 3600 + m * 60 + sec


def vparse_date(s: pl.Series) -> pl.Series:
    if not isinstance(s, pl.Series):
        s = pl.Series(s)

    # If already a Date type, return as-is
    if s.dtype == pl.Date:
        return s

    return s.str.strptime(pl.Date, DATE_FORMAT, strict=False)
