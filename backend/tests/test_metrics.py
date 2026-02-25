import polars as pl
from datetime import date
from src.metrics import (
    format_rows,
    get_top_bot,
    compute_diff_metrics,
    compute_consistency_metrics,
)


def test_format_rows():
    df = pl.DataFrame(
        {
            "station_id": ["A", "B"],
            "station_name": ["Station A", "Station B"],
            "state": ["CO", "WA"],
            "elevation_m": [1000, 2000],
            "snow_depth_m": [1.2345, 2.3456],
            "year": [2021, 2022],
        }
    )

    rows = format_rows(df, "snow_depth_m", round_digits=2, extra_cols=["year"])

    assert len(rows) == 2
    assert rows[0]["value"] == 1.23
    assert rows[0]["year"] == 2021
    assert rows[0]["name"] == "Station A"


def test_get_top_bot():
    df = pl.DataFrame(
        {
            "station_id": ["A", "B", "C", "D"],
            "station_name": ["A", "B", "C", "D"],
            "state": ["CO", "CO", "CO", "CO"],
            "elevation_m": [1, 2, 3, 4],
            "val": [10.0, 5.0, 1.0, 20.0],
        }
    )

    res = get_top_bot(df, "val", top_n=2, bot_n=2)
    assert res["total_count"] == 4
    # Top should be D (20), A (10)
    assert res["top"][0]["station_id"] == "D"
    assert res["top"][1]["station_id"] == "A"
    # Bot should be C (1), B (5) - hmm, let's check sorting
    assert res["bottom"][-1]["station_id"] == "C"


def test_compute_diff_metrics():
    df = pl.DataFrame(
        {
            "station_id": ["A", "A", "A"],
            "datetime": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
            "snow_depth_m": [1.0, 1.5, 1.2],
        }
    )

    cutoff = date(2023, 1, 2)
    res = compute_diff_metrics(df, cutoff)

    assert res.height == 1
    assert res.select("snow_depth_m").item() == 1.2
    # 24h diff: 1.2 - 1.5 = -0.3
    assert abs(res.select("snow_depth_24h_diff").item() - (-0.3)) < 0.001
    # 48h diff: 1.2 - 1.0 = 0.2
    assert abs(res.select("snow_depth_48h_diff").item() - 0.2) < 0.001


def test_compute_consistency_metrics():
    df = pl.DataFrame(
        {
            "station_id": ["A"] * 6,
            "water_year": [2000, 2001, 2002, 2003, 2004, 2005],
            "snow_depth_m": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )

    res = compute_consistency_metrics(df, min_observations_per_year=1)

    assert res.height == 1
    assert res.select("wy_count").item() == 6
    assert res.select("all_time_max").item() == 6.0
    assert res.select("all_time_max_year").item() == 2005
    assert res.select("all_time_min").item() == 1.0
    assert res.select("all_time_min_year").item() == 2000
