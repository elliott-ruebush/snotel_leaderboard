import json
from datetime import datetime, timedelta, timezone
import polars as pl
from snotel_lib import SnotelClient
from snotel_lib.clean import DEFAULT_CHECKS, QCLogSchema, run_qc
from snotel_lib.schemas import AllSnotelDataSchema, SnotelDataSchema, StationMetadataSchema

from .metrics import (
    compute_diff_metrics,
    compute_consistency_metrics,
    compute_live_z_score,
    get_top_bot,
)


def get_station_metadata(client: SnotelClient) -> pl.DataFrame:
    metadata_gdf = client.get_stations_metadata()
    metadata_df = pl.from_pandas(metadata_gdf.drop(columns="geometry").reset_index())

    return metadata_df.filter(pl.col(StationMetadataSchema.network) == "SNOTEL").select(
        [
            pl.col(StationMetadataSchema.code).alias(AllSnotelDataSchema.station_id),
            pl.col(StationMetadataSchema.name).alias("station_name"),
            pl.col(StationMetadataSchema.state),
            pl.col(StationMetadataSchema.elevation_m),
        ]
    )


def prepare_station_data(client: SnotelClient) -> pl.DataFrame:
    df = client.get_all_station_data()
    df = df.drop_nulls(
        subset=[SnotelDataSchema.datetime, AllSnotelDataSchema.station_id]
    ).sort([AllSnotelDataSchema.station_id, SnotelDataSchema.datetime])

    # Run QC checks
    # Provide a generic station argument since we're processing all at once
    # We will compute flags per row. Usually run_qc generates a side log per station,
    # but here we can just use it to filter the dataframe cleanly based on DEFAULT_CHECKS.
    qc_result = run_qc(df, "ALL_STATIONS", DEFAULT_CHECKS)
    df = qc_result.data
    qc_logs = qc_result.qc

    # For the leaderboard, we are only tagging a station's *latest* observation as flagged
    # if it triggered a flag.
    flagged_station_dates = (
        qc_logs.group_by([QCLogSchema.station_id, QCLogSchema.datetime])
        .agg(pl.col(QCLogSchema.explanation).unique().alias("qc_flags"))
        .with_columns(pl.lit(True).alias("is_flagged"))
    )

    df = df.join(
        flagged_station_dates,
        on=[AllSnotelDataSchema.station_id, SnotelDataSchema.datetime],
        how="left",
    ).with_columns(
        [
            pl.col("is_flagged").fill_null(False),
            pl.col("qc_flags").fill_null([]),
        ]
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
    min_date = df.select(pl.col(SnotelDataSchema.datetime).min()).to_series()[0].isoformat()
    max_date = df.select(pl.col(SnotelDataSchema.datetime).max()).to_series()[0].isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()
    total_stations = (
        metadata_df.select(pl.col(AllSnotelDataSchema.station_id).n_unique()).to_series()[0]
    )

    recent_cutoff = df.select(pl.col(SnotelDataSchema.datetime).max()).to_series()[0] - timedelta(
        days=7
    )

    latest_diff_df = compute_diff_metrics(df, recent_cutoff)
    consistency_df = compute_consistency_metrics(df)
    anomaly_df = compute_live_z_score(df)

    latest_diff_df = latest_diff_df.join(
        metadata_df, on=AllSnotelDataSchema.station_id, how="inner"
    )
    consistency_df = consistency_df.join(
        metadata_df, on=AllSnotelDataSchema.station_id, how="inner"
    )
    anomaly_df = anomaly_df.join(
        metadata_df, on=AllSnotelDataSchema.station_id, how="inner"
    )

    leaderboard = {
        "metadata": {
            "generated_at": generated_at,
            "min_date": min_date,
            "max_date": max_date,
            "total_stations": total_stations,
            "units": {
                "depth": "meter",
                "swe": "meter",
                "elevation": "meter",
                "temperature": "degree_Celsius",
            },
        }
    }

    leaderboard["base_builders"] = get_top_bot(latest_diff_df, "snow_depth_m")
    leaderboard["water_bearers"] = get_top_bot(latest_diff_df, "swe_m")
    leaderboard["deepest_dumps_24h"] = get_top_bot(
        latest_diff_df, "snow_depth_24h_diff"
    )
    leaderboard["swe_trend_24h"] = get_top_bot(latest_diff_df, "swe_24h_diff")

    leaderboard["deepest_dumps_48h"] = get_top_bot(
        latest_diff_df, "snow_depth_48h_diff"
    )
    leaderboard["swe_trend_48h"] = get_top_bot(latest_diff_df, "swe_48h_diff")

    leaderboard["deepest_dumps_7d"] = get_top_bot(latest_diff_df, "snow_depth_7d_diff")
    leaderboard["swe_trend_7d"] = get_top_bot(latest_diff_df, "swe_7d_diff")

    leaderboard["historical_consistency"] = get_top_bot(
        consistency_df,
        "std_dev",
        extra_cols=[
            "all_time_max",
            "all_time_max_year",
            "all_time_min",
            "all_time_min_year",
        ],
    )

    leaderboard["live_z_score"] = get_top_bot(
        anomaly_df,
        "live_z_score",
        sort_by="abs_z_score",
        round_digits=2,
        extra_cols=["hist_mean_swe", "current_swe"],
    )

    leaderboard["historical_consistency"]["notes"] = (
        "Data cleaned: Snow depth > 15m (sensor error) filtered; negative readings zeroed. "
        "Consistency metrics require at least 5 years of 'full' data (>= 330 daily observations per water year)."
    )
    leaderboard["live_z_score"]["notes"] = (
        "Live Z-score is comparing current SWE to historical SWE for the exact same calendar day of the year. "
        "(Most anomalous positive / negative vs most on trend near 0)."
    )

    output_file = "../frontend/public/leaderboard.json"
    with open(output_file, "w") as f:
        json.dump(leaderboard, f, indent=2)

    print(f"Exported leaderboard to {output_file}")


if __name__ == "__main__":
    generate_leaderboard()
