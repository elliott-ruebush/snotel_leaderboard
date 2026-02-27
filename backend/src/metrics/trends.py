import polars as pl


def compute_diff_metrics(df: pl.DataFrame, recent_cutoff) -> pl.DataFrame:
    diff_df = df.with_columns(
        [
            (
                pl.col("snow_depth_m")
                - pl.col("snow_depth_m").shift(1).over("station_id")
            ).alias("snow_depth_24h_diff"),
            (
                pl.col("snow_depth_m")
                - pl.col("snow_depth_m").shift(2).over("station_id")
            ).alias("snow_depth_48h_diff"),
            (
                pl.col("snow_depth_m")
                - pl.col("snow_depth_m").shift(7).over("station_id")
            ).alias("snow_depth_7d_diff"),
            (pl.col("swe_m") - pl.col("swe_m").shift(1).over("station_id")).alias(
                "swe_24h_diff"
            ),
            (pl.col("swe_m") - pl.col("swe_m").shift(2).over("station_id")).alias(
                "swe_48h_diff"
            ),
            (pl.col("swe_m") - pl.col("swe_m").shift(7).over("station_id")).alias(
                "swe_7d_diff"
            ),
        ]
    )
    return (
        diff_df.filter(pl.col("datetime") >= recent_cutoff)
        .group_by("station_id")
        .last()
    )
