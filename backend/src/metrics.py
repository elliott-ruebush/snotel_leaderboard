import polars as pl


def format_rows(
    df: pl.DataFrame,
    metric_col: str,
    round_digits: int = 3,
    extra_cols: list[str] | None = None,
) -> list[dict]:
    res = []
    for r in df.to_dicts():
        row = {
            "station_id": r.get("station_id"),
            "name": r.get("station_name", "Unknown"),
            "state": r.get("state", "Unknown"),
            "elevation_m": r.get("elevation_m"),
            "value": round(r.get(metric_col, 0), round_digits)
            if r.get(metric_col) is not None
            else None,
        }
        if extra_cols:
            for ecol in extra_cols:
                if ecol.endswith("_year"):
                    row[ecol] = r.get(ecol)
                else:
                    row[ecol] = (
                        round(r.get(ecol, 0), round_digits)
                        if r.get(ecol) is not None
                        else None
                    )
        res.append(row)
    return res


def get_top_bot(
    df: pl.DataFrame, col: str, top_n: int = 10, bot_n: int = 5, **kwargs
) -> dict:
    valid_df = df.drop_nulls([col])
    total = valid_df.height
    top = valid_df.sort(col, descending=True).head(top_n)
    bot = valid_df.sort(col, descending=True).tail(bot_n)
    return {
        "top": format_rows(top, col, **kwargs),
        "bottom": format_rows(bot, col, **kwargs),
        "total_count": total,
    }


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
