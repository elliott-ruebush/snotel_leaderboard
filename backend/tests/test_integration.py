from pathlib import Path
import polars as pl
import geopandas as gpd
from shapely.geometry import Point
from src.generate_leaderboard import generate_leaderboard
from snotel_lib.schemas import StationMetadataSchema


def test_generate_leaderboard_smoke(mocker, tmp_path: Path, sample_all_station_data: pl.DataFrame):
    """
    Integration test for the main generation script.
    Mocks the client to prevent network access and verifies JSON export.
    """
    # 1. Setup paths
    frontend_dir = tmp_path / "frontend"
    public_dir = frontend_dir / "public"
    public_dir.mkdir(parents=True)

    # 2. Mock SnotelClient
    mock_client_instance = mocker.Mock()

    # Mock metadata (using pandas because SnotelClient returns GDF)
    gdf = gpd.GeoDataFrame(
        {
            StationMetadataSchema.station_id: ["A", "B"],
            StationMetadataSchema.station_name: ["Station A", "Station B"],
            StationMetadataSchema.network: ["SNOTEL", "SNOTEL"],
            StationMetadataSchema.state: ["CO", "WA"],
            StationMetadataSchema.elevation_m: [1000, 2000],
        },
        geometry=[Point(0, 0), Point(1, 1)],
    )

    mock_client_instance.get_stations_metadata.return_value = gdf
    mock_client_instance.get_all_station_data.return_value = sample_all_station_data

    mocker.patch(
        "src.generate_leaderboard.EgagliClient", return_value=mock_client_instance
    )

    # Patch the output file path to use our tmp directory
    # We use a real file handle or mock it. The current test uses a mock.
    m_open = mocker.mock_open()
    mocker.patch("builtins.open", m_open)

    # 3. Run
    generate_leaderboard()

    # 4. Verify
    # The script uses a relative path from the CWD. By default CWD is repo root in pytest.
    # The actual code has LEADERBOARD_EXPORT_PATH = "../frontend/public/leaderboard.json"
    m_open.assert_called_with("../frontend/public/leaderboard.json", "w")
