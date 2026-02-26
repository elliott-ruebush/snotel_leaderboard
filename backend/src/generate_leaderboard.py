import json
from datetime import datetime, timedelta, timezone
import polars as pl
from snotel_lib import SnotelClient

from metrics import compute_diff_metrics, compute_consistency_metrics, get_top_bot


def get_station_metadata(client: SnotelClient) -> pl.DataFrame:
    metadata_gdf = client.get_stations_metadata()
    metadata_df = pl.from_pandas(metadata_gdf.drop(columns="geometry").reset_index())

    return metadata_df.filter(pl.col("network") == "SNOTEL").select(
        [
            pl.col("code").alias("station_id"),
            pl.col("name").alias("station_name"),
            pl.col("state"),
            pl.col("elevation_m"),
        ]
    )


def prepare_station_data(client: SnotelClient) -> pl.DataFrame:
    df = client.get_all_station_data()
    df = df.drop_nulls(subset=["datetime", "station_id"]).sort(
        ["station_id", "datetime"]
    )

    df = df.with_columns(
        pl.when(pl.col("snow_depth_m") < 0)
        .then(0.0)
        .when(pl.col("snow_depth_m") > 15)
        .then(None)
        .otherwise(pl.col("snow_depth_m"))
        .alias("snow_depth_m")
    )

    df = df.with_columns(
        pl.when(pl.col("datetime").dt.month() >= 10)
        .then(pl.col("datetime").dt.year() + 1)
        .otherwise(pl.col("datetime").dt.year())
        .alias("water_year")
    )

    return df


def generate_leaderboard():
    client = SnotelClient()

    print("Fetching station metadata...")
    metadata_df = get_station_metadata(client)

    print("Fetching combined station data...")
    df = prepare_station_data(client)

    print("Computing metrics...")
    min_date = df.select(pl.col("datetime").min()).to_series()[0].isoformat()
    max_date = df.select(pl.col("datetime").max()).to_series()[0].isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()
    total_stations = metadata_df.select(pl.col("station_id").n_unique()).to_series()[0]

    recent_cutoff = df.select(pl.col("datetime").max()).to_series()[0] - timedelta(
        days=7
    )

    latest_diff_df = compute_diff_metrics(df, recent_cutoff)
    consistency_df = compute_consistency_metrics(df)

    latest_diff_df = latest_diff_df.join(metadata_df, on="station_id", how="inner")
    consistency_df = consistency_df.join(metadata_df, on="station_id", how="inner")

    leaderboard = {
        "metadata": {
            "generated_at": generated_at,
            "min_date": min_date,
            "max_date": max_date,
            "total_stations": total_stations,
        }
    }

    leaderboard["base_builders"] = get_top_bot(latest_diff_df, "snow_depth_m")
    leaderboard["water_bearers"] = get_top_bot(latest_diff_df, "swe_m")
    leaderboard["deepest_dumps_24h"] = get_top_bot(
        latest_diff_df, "snow_depth_24h_diff"
    )
    leaderboard["deepest_dumps_48h"] = get_top_bot(
        latest_diff_df, "snow_depth_48h_diff"
    )
    leaderboard["deepest_dumps_7d"] = get_top_bot(latest_diff_df, "snow_depth_7d_diff")

    leaderboard["historical_consistency"] = get_top_bot(
        consistency_df,
        "std_dev",
        round_digits=4,
        extra_cols=[
            "all_time_max",
            "all_time_max_year",
            "all_time_min",
            "all_time_min_year",
        ],
    )

    leaderboard["historical_consistency"]["notes"] = (
        "Data cleaned: Snow depth > 15m (sensor error) filtered; negative readings zeroed. "
        "Consistency metrics require at least 5 years of 'full' data (>= 330 daily observations per water year)."
    )

    output_file = "../frontend/public/leaderboard.json"
    with open(output_file, "w") as f:
        json.dump(leaderboard, f, indent=2)

    print(f"Exported leaderboard to {output_file}")


if __name__ == "__main__":
    generate_leaderboard()
