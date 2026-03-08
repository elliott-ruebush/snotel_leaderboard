import json
from datetime import UTC, datetime, timedelta

import polars as pl
from snotel_lib import SnotelClient
from snotel_lib.validation import DEFAULT_FILTERS, DEFAULT_FLAGS, QCLogSchema, run_qc
from snotel_lib.schemas import (
    AllSnotelDataSchema,
    SnotelDataSchema,
    StationMetadataSchema,
)

from .metrics import (
    compute_consistency_metrics,
    compute_diff_metrics,
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
    # 1. Fetch and sort
    df = (
        client.get_all_station_data()
        .drop_nulls(subset=[SnotelDataSchema.datetime, AllSnotelDataSchema.station_id])
        .sort([AllSnotelDataSchema.station_id, SnotelDataSchema.datetime])
    )

    # 2. Apply QC
    qc = run_qc(df, DEFAULT_FILTERS, DEFAULT_FLAGS)

    # 3. Aggregate flags
    flag_summary = (
        pl.concat([qc.filter_log, qc.flag_log])
        .group_by([QCLogSchema.station_id, QCLogSchema.datetime])
        .agg(pl.col(QCLogSchema.explanation).unique().alias("qc_flags"))
    )

    # 4. Join and with flags and enrich with water years
    return (
        qc.data.join(
            flag_summary,
            on=[AllSnotelDataSchema.station_id, SnotelDataSchema.datetime],
            how="left",
        )
        .with_columns(
            is_flagged=pl.col("qc_flags").is_not_null(),
            qc_flags=pl.col("qc_flags").fill_null(pl.lit([], dtype=pl.List(pl.String))),
            water_year=pl.col(SnotelDataSchema.datetime).dt.year()
            + (pl.col(SnotelDataSchema.datetime).dt.month() >= 10).cast(pl.Int32),
        )
    )


def generate_leaderboard():
    client = SnotelClient()

    print("Fetching station metadata...")
    metadata_df = get_station_metadata(client)

    print("Fetching combined station data...")
    df = prepare_station_data(client)

    print("Computing metrics...")
    # Cutoff for 'recent' leaderboard entries
    latest_date = df.select(pl.col(SnotelDataSchema.datetime).max()).item()
    recent_cutoff = latest_date - timedelta(days=7)
    # Run heavy derivations
    latest_diff_df = compute_diff_metrics(df, recent_cutoff)
    consistency_df = compute_consistency_metrics(df)
    anomaly_df = compute_live_z_score(df)

    # Join metadata to results
    latest_diff_df, consistency_df, anomaly_df = [
        m_df.join(metadata_df, on=AllSnotelDataSchema.station_id, how="inner")
        for m_df in [latest_diff_df, consistency_df, anomaly_df]
    ]

    # Build response structure
    leaderboard = {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "min_date": df.select(pl.col(SnotelDataSchema.datetime).min()).item().isoformat(),
            "max_date": latest_date.isoformat(),
            "total_stations": metadata_df.select(pl.col(AllSnotelDataSchema.station_id).n_unique()).item(),
            "units": {
                "depth": "meter",
                "swe": "meter",
                "elevation": "meter",
                "temperature": "degree_Celsius",
            },
        },
        "base_builders": get_top_bot(latest_diff_df, "snow_depth_m"),
        "water_bearers": get_top_bot(latest_diff_df, "swe_m"),
        "deepest_dumps_24h": get_top_bot(latest_diff_df, "snow_depth_24h_diff"),
        "swe_trend_24h": get_top_bot(latest_diff_df, "swe_24h_diff"),
        "deepest_dumps_48h": get_top_bot(latest_diff_df, "snow_depth_48h_diff"),
        "swe_trend_48h": get_top_bot(latest_diff_df, "swe_48h_diff"),
        "deepest_dumps_7d": get_top_bot(latest_diff_df, "snow_depth_7d_diff"),
        "swe_trend_7d": get_top_bot(latest_diff_df, "swe_7d_diff"),
        "historical_consistency": get_top_bot(
            consistency_df,
            "std_dev",
            extra_cols=["all_time_max", "all_time_max_year", "all_time_min", "all_time_min_year"],
        ),
        "live_z_score": get_top_bot(
            anomaly_df,
            "live_z_score",
            sort_by="abs_z_score",
            round_digits=2,
            extra_cols=["hist_mean_swe", "current_swe"],
        ),
    }

    leaderboard["historical_consistency"]["notes"] = (
        "Consistency metrics require at least 5 years of 'full' data (>= 330 daily observations per water year)."
    )
    leaderboard["live_z_score"]["notes"] = (
        "Compares current SWE to historical average SWE for the exact same calendar day of the year. "
        "Top stations are much higher/lower than average while bottom stations are closest to average"
    )

    output_file = "../frontend/public/leaderboard.json"
    with open(output_file, "w") as f:
        json.dump(leaderboard, f, indent=2)

    print(f"Exported leaderboard to {output_file}")


if __name__ == "__main__":
    generate_leaderboard()
