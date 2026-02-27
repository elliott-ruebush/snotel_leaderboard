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
        dt = r.get("datetime")
        if dt is not None:
            row["data_date"] = str(dt)
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
    df: pl.DataFrame,
    col: str,
    top_n: int = 10,
    bot_n: int = 5,
    sort_by: str | None = None,
    **kwargs,
) -> dict:
    valid_df = df.drop_nulls([col])
    if sort_by is None:
        sort_by = col

    total = valid_df.height
    top = valid_df.sort(sort_by, descending=True).head(top_n)
    bot = valid_df.sort(sort_by, descending=True).tail(bot_n)
    return {
        "top": format_rows(top, col, **kwargs),
        "bottom": format_rows(bot, col, **kwargs),
        "total_count": total,
    }
