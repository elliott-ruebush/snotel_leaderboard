import pytest
import polars as pl
from datetime import date
from snotel_lib.schemas import AllSnotelDataSchema, SnotelDataSchema


@pytest.fixture
def sample_all_station_data():
    """Returns a basic Polars DataFrame mirroring get_all_station_data output."""
    return pl.DataFrame(
        {
            AllSnotelDataSchema.station_id: ["A", "B"],
            SnotelDataSchema.datetime: [date(2023, 1, 1), date(2023, 1, 1)],
            SnotelDataSchema.snow_depth_m: [1.2345, 2.3456],
            SnotelDataSchema.swe_m: [0.1, 0.2],
            SnotelDataSchema.precip_m: [0.1, 0.2],
            SnotelDataSchema.tavg_c: [1.0, 2.0],
            SnotelDataSchema.tmin_c: [0.0, 1.0],
            SnotelDataSchema.tmax_c: [2.0, 3.0],
        }
    )
