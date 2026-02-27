import polars as pl


def compute_consistency_metrics(
    df: pl.DataFrame, min_observations_per_year: int = 330
) -> pl.DataFrame:
    yearly_df = df.group_by(["station_id", "water_year"]).agg(
        [
            pl.col("snow_depth_m").max().alias("yearly_max_depth"),
            pl.col("snow_depth_m").is_not_null().sum().alias("obs_count"),
        ]
    )

    valid_yearly_df = yearly_df.filter(
        (pl.col("yearly_max_depth").is_not_null())
        & (pl.col("obs_count") >= min_observations_per_year)
    ).sort(["station_id", "yearly_max_depth"])

    return (
        valid_yearly_df.group_by("station_id")
        .agg(
            pl.col("yearly_max_depth").std().alias("std_dev"),
            pl.col("yearly_max_depth").last().alias("all_time_max"),
            pl.col("water_year").last().alias("all_time_max_year"),
            pl.col("yearly_max_depth").first().alias("all_time_min"),
            pl.col("water_year").first().alias("all_time_min_year"),
            pl.col("yearly_max_depth").count().alias("wy_count"),
        )
        .filter(pl.col("wy_count") >= 5)
    )
