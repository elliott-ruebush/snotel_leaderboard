import polars as pl
from datetime import date
import datetime
from src.metrics import (
    format_rows,
    get_top_bot,
    compute_diff_metrics,
    compute_consistency_metrics,
    compute_live_z_score,
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
            "abs_val": [10.0, 5.0, 1.0, 20.0],
        }
    )

    res = get_top_bot(df, "val", top_n=2, bot_n=2, sort_by="abs_val")
    assert res["total_count"] == 4
    # Top should be D (20), A (10)
    assert res["top"][0]["station_id"] == "D"
    assert res["top"][1]["station_id"] == "A"
    # Bot should be C (1), B (5)
    assert res["bottom"][-1]["station_id"] == "C"


def test_compute_diff_metrics():
    df = pl.DataFrame(
        {
            "station_id": ["A", "A", "A", "A", "A", "A", "A", "A"],
            "datetime": [date(2023, 1, i) for i in range(1, 9)],
            "snow_depth_m": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5],
            "swe_m": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.3],
        }
    )

    cutoff = date(2023, 1, 7)
    res = compute_diff_metrics(
        df.with_columns(pl.col("datetime").cast(pl.Date)), cutoff
    )

    assert res.height == 1

    # 24h prior is day 7
    diff24_snow = res.select("snow_depth_24h_diff").item()
    assert abs(diff24_snow - 0.5) < 0.001

    diff24_swe = res.select("swe_24h_diff").item()
    assert abs(diff24_swe - 0.2) < 0.001


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


def test_compute_live_z_score():
    # 6 years of data on Jan 1st.
    df = pl.DataFrame(
        {
            "station_id": ["A"] * 6,
            "datetime": [
                datetime.date(2020, 1, 1),
                datetime.date(2021, 1, 1),
                datetime.date(2022, 1, 1),
                datetime.date(2023, 1, 1),
                datetime.date(2024, 1, 1),
                datetime.date(2025, 1, 1),  # Latest observation
            ],
            "swe_m": [1.0, 1.2, 0.8, 1.1, 0.9, 1.5],  # mean=1.0, std=0.158
            "snow_depth_m": [1.0] * 6,
        }
    )

    res = compute_live_z_score(df)
    assert len(res) == 1

    z_score = res.select("live_z_score").item()
    # Math:
    # 2020: 1.0, 2021: 1.2, 2022: 0.8, 2023: 1.1, 2024: 0.9 -> Mean 1.0, std_dev = sqrt(0.1/4) = 0.158113883
    # 2025: 1.5 -> (1.5 - 1.0) / 0.158113883 = 3.162

    assert abs(z_score - 3.162) < 0.01


def test_compute_live_z_score_zero_variance():
    # 6 years of data where SWE is exactly the same, resulting in 0 variance
    df = pl.DataFrame(
        {
            "station_id": ["B"] * 6,
            "datetime": [
                datetime.date(2020, 1, 1),
                datetime.date(2021, 1, 1),
                datetime.date(2022, 1, 1),
                datetime.date(2023, 1, 1),
                datetime.date(2024, 1, 1),
                datetime.date(2025, 1, 1),
            ],
            "swe_m": [1.0, 1.0, 1.0, 1.0, 1.0, 1.5],  # Hist mean=1.0, std=0.0
            "snow_depth_m": [1.0] * 6,
        }
    )

    res = compute_live_z_score(df)
    # Because standard deviation is zero, the live_z_score would be inf/NaN
    # Our function is designed to filter out non-finite z-scores.
    assert len(res) == 0


def test_compute_live_z_score_staleness_filter():
    """
    Regression test for the Skookum Creek bug: a station with stale cache data
    (last reading months before the global max date) was generating spurious high
    Z-scores because the "current" reading was from a snow-free period, compared
    against historically snow-free historical days.

    We use two stations here:
    - Station A: recent, up to the global max date 2026-02-26
    - Station B: stale, last reading is 2025-10-01 (~150 days behind)

    Station B should be excluded from Z-score results.
    """
    # Station A has 6 years of Feb-26 data and a current reading on 2026-02-26
    station_a = pl.DataFrame(
        {
            "station_id": ["A"] * 6,
            "datetime": [
                datetime.date(2020, 2, 26),
                datetime.date(2021, 2, 26),
                datetime.date(2022, 2, 26),
                datetime.date(2023, 2, 26),
                datetime.date(2024, 2, 26),
                datetime.date(2026, 2, 26),  # Current
            ],
            "swe_m": [0.4, 0.5, 0.45, 0.6, 0.35, 0.47],
            "snow_depth_m": [1.0] * 6,
        }
    )

    # Station B's last reading is from 2025-10-01 (stale — ~150 days before global max)
    station_b = pl.DataFrame(
        {
            "station_id": ["B"] * 6,
            "datetime": [
                datetime.date(2020, 10, 1),
                datetime.date(2021, 10, 1),
                datetime.date(2022, 10, 1),
                datetime.date(2023, 10, 1),
                datetime.date(2024, 10, 1),
                datetime.date(2025, 10, 1),  # "Current" but stale vs global 2026-02-26
            ],
            "swe_m": [0.0, 0.01, 0.0, 0.02, 0.0, 0.01],  # Near-zero early-season
            "snow_depth_m": [0.0] * 6,
        }
    )

    df = pl.concat([station_a, station_b])
    res = compute_live_z_score(df, max_staleness_days=14)

    # Station B should be excluded; only Station A should appear
    station_ids = res.select("station_id").to_series().to_list()
    assert "B" not in station_ids, "Stale station B should have been excluded"
    assert "A" in station_ids, "Recent station A should be included"
