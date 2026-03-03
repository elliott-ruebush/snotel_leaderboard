import pytest
import polars as pl
from datetime import date


@pytest.fixture
def sample_station_df():
    """Returns a basic Polars DataFrame for metric testing."""
    return pl.DataFrame(
        {
            "station_id": ["A", "B"],
            "station_name": ["Station A", "Station B"],
            "state": ["CO", "WA"],
            "elevation_m": [1000, 2000],
            "snow_depth_m": [1.2345, 2.3456],
            "swe_m": [0.1, 0.2],
            "datetime": [date(2023, 1, 1), date(2023, 1, 1)],
            "water_year": [2023, 2023],
        }
    )
