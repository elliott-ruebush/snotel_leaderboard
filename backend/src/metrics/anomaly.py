import polars as pl
from datetime import timedelta


def compute_live_z_score(df: pl.DataFrame, max_staleness_days: int = 7) -> pl.DataFrame:
    """
    Compute the Live Z-score for the most recent observation of each station.
    Z-score = (Current SWE - Historical SWE for the same Day-of-Year) / Historical Std for that Day-of-Year.

    Stations whose most recent reading is more than `max_staleness_days` behind the
    global dataset max date are excluded to avoid spurious anomalies from stale cache entries.
    """
    df_valid = df.filter(pl.col("swe_m").is_not_null())

    # Compute the global max date across ALL stations
    global_max_date = df_valid.select(pl.col("datetime").max()).item()
    staleness_cutoff = global_max_date - timedelta(days=max_staleness_days)

    # 1. Get the latest observation for each station, filtered to only recent stations
    latest_df = (
        df_valid.sort("datetime")
        .group_by("station_id")
        .last()
        .filter(pl.col("datetime") >= staleness_cutoff)
    )

    # 2. Extract month, day, and current value for the latest observation
    latest_info = latest_df.select(
        [
            "station_id",
            "datetime",
            pl.col("datetime").dt.month().alias("target_month"),
            pl.col("datetime").dt.day().alias("target_day"),
            pl.col("swe_m").alias("current_swe"),
        ]
    )

    # 3. Add month and day to the entire dataframe for joining
    df_with_md = df_valid.with_columns(
        [
            pl.col("datetime").dt.month().alias("month"),
            pl.col("datetime").dt.day().alias("day"),
        ]
    )

    # 4. Join historical data with latest info on station and month/day
    joined_df = df_with_md.join(
        latest_info,
        left_on=["station_id", "month", "day"],
        right_on=["station_id", "target_month", "target_day"],
        how="inner",
    )

    latest_datetimes = latest_df.select(
        ["station_id", pl.col("datetime").alias("latest_datetime")]
    )
    joined_df = joined_df.join(latest_datetimes, on="station_id")

    hist_df = joined_df.filter(pl.col("datetime") < pl.col("latest_datetime"))

    # 5. Calculate mean and std
    stats_df = hist_df.group_by("station_id").agg(
        [
            pl.col("swe_m").mean().alias("hist_mean_swe"),
            pl.col("swe_m").std().alias("hist_std_swe"),
            pl.col("swe_m").count().alias("hist_count"),
        ]
    )

    # Require at least 5 years of historical data for that specific day
    stats_df = stats_df.filter(pl.col("hist_count") >= 5)

    # 6. Join back to current swe and compute z-score
    result_df = latest_info.join(stats_df, on="station_id", how="inner")

    result_df = result_df.with_columns(
        (
            (pl.col("current_swe") - pl.col("hist_mean_swe")) / pl.col("hist_std_swe")
        ).alias("live_z_score")
    )

    result_df = result_df.with_columns(
        pl.col("live_z_score").abs().alias("abs_z_score")
    )

    return result_df.filter(
        pl.col("live_z_score").is_not_null() & pl.col("live_z_score").is_finite()
    )
