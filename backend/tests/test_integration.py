from src.generate_leaderboard import generate_leaderboard


def test_generate_leaderboard_smoke(mocker, tmp_path, sample_station_df):
    """
    Integration test for the main generation script.
    Mocks the client to prevent network access and verifies JSON export.
    """
    # 1. Setup paths
    frontend_dir = tmp_path / "frontend"
    public_dir = frontend_dir / "public"
    public_dir.mkdir(parents=True)

    # Mock the output path in generate_leaderboard
    # Since it's hardcoded as relative path, we'll patch it if possible or
    # rely on the fact that we can control the CWD.

    # 2. Mock SnotelClient
    mock_client_instance = mocker.Mock()

    # Mock metadata (using pandas because SnotelClient returns GDF)
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {
            "code": ["A", "B"],
            "name": ["Station A", "Station B"],
            "network": ["SNOTEL", "SNOTEL"],
            "state": ["CO", "WA"],
            "elevation_m": [1000, 2000],
        },
        geometry=[Point(0, 0), Point(1, 1)],
    )
    gdf.set_index("code", inplace=True)

    mock_client_instance.get_stations_metadata.return_value = gdf
    mock_client_instance.get_all_station_data.return_value = sample_station_df

    mocker.patch(
        "src.generate_leaderboard.EgagliClient", return_value=mock_client_instance
    )

    # Patch the output file path to use our tmp directory
    mocker.patch("builtins.open", mocker.mock_open())

    # 3. Run
    generate_leaderboard()

    # 4. Verify
    import builtins

    builtins.open.assert_called_with("../frontend/public/leaderboard.json", "w")
