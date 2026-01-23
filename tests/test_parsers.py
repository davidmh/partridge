import datetime
import math
import polars as pl
import pytest
from partridge.parsers import parse_time, parse_date, vparse_time, vparse_date


def test_parse_date():
    assert parse_date("20990101") == datetime.date(2099, 1, 1)


def test_parse_date_with_invalid_month():
    with pytest.raises(ValueError, match=r"unconverted data remains: 01"):
        parse_date("20991401")


def test_parse_date_with_invalid_day():
    with pytest.raises(ValueError, match=r"unconverted data remains: 3"):
        parse_date("20990133")


def test_vparse_date():
    datestrs = ["20990101", "20990102"]
    dateobjs = [datetime.date(2099, 1, 1), datetime.date(2099, 1, 2)]

    result = vparse_date(pl.Series(datestrs))
    expected = pl.Series(dateobjs)

    assert result.equals(expected)


def test_parse_time():
    val = parse_time(float("nan"))
    assert val is not None and math.isnan(val)

    val = parse_time("")
    assert val is not None and math.isnan(val)

    val = parse_time("  ")
    assert val is not None and math.isnan(val)

    assert parse_time("00:00:00") == 0
    assert parse_time("0:00:00") == 0
    assert parse_time("01:02:03") == 3723
    assert parse_time("1:02:03") == 3723
    assert parse_time("25:24:23") == 91463
    assert parse_time("250:24:23") == 901463


def test_parse_time_with_invalid_input():
    with pytest.raises(ValueError, match=r"invalid literal for int()"):
        parse_time("10:15:00am")


def test_vparse_time():
    timestrs = ["00:00:00", "250:24:23"]
    timeints = [0.0, 901463.0]

    result = vparse_time(pl.Series(timestrs))
    expected = pl.Series(timeints)

    assert result.equals(expected)


def test_vparse_time_already_parsed():
    """vparse_time should handle already-parsed numeric values."""
    timeints = [0.0, 901463.0, 3723.0]
    series = pl.Series(timeints)

    result = vparse_time(series)

    assert result.dtype == pl.Float64
    assert result.equals(series)


def test_vparse_date_already_parsed():
    """vparse_date should handle already-parsed date values."""
    dateobjs = [datetime.date(2099, 1, 1), datetime.date(2099, 1, 2)]
    series = pl.Series(dateobjs)

    result = vparse_date(series)

    assert result.dtype == pl.Date
    assert result.equals(series)
