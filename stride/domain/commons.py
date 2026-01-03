import polars as pl


def _calculate_zones(df: pl.DataFrame) -> pl.DataFrame:
    """Calculate and add zone percentages from raw zone seconds."""
    return (
        df.with_columns(
            pl.sum_horizontal("z1_s", "z2_s", "z3_s", "z4_s", "z5_s").alias("total_s")
        )
        .with_columns(
            (pl.col("z1_s") / pl.col("total_s")).alias("z1_pct"),
            (pl.col("z2_s") / pl.col("total_s")).alias("z2_pct"),
            (pl.col("z3_s") / pl.col("total_s")).alias("z3_pct"),
            (pl.col("z4_s") / pl.col("total_s")).alias("z4_pct"),
            (pl.col("z5_s") / pl.col("total_s")).alias("z5_pct"),
        )
        .drop(["z1_s", "z2_s", "z3_s", "z4_s", "z5_s", "total_s"])
    )
