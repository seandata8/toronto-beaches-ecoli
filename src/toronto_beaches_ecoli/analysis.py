"""The analysis the paper runs, as functions.

Both the check against simulated data, where the answer is known, and the
analysis of the real data call these, so the two cannot drift apart. The design
is set out in `other/notes/analysis_plan.md`.
"""

import numpy as np
import polars as pl
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

WARNING_THRESHOLD = 100
DETECTION_LIMIT = 10
MINIMUM_RESULTS = 4


def daily_geometric_means(
    results: pl.DataFrame, minimum_results: int = MINIMUM_RESULTS
) -> pl.DataFrame:
    """One geometric mean per beach per day, on the log10 scale.

    The geometric mean is the mean of the logarithms, converted back. It is the
    figure Toronto's limit applies to. A day needs `minimum_results` samples:
    four, not five, so that Sunnyside's four sites are included.
    """
    return (
        results.with_columns(pl.col("eColi").log10().alias("logEColi"))
        .group_by("beachName", "collectionDate")
        .agg(
            pl.col("logEColi").mean().alias("logGeometricMean"),
            pl.len().alias("nResults"),
            # A day is at the floor only when every sample was.
            (pl.col("eColi") <= DETECTION_LIMIT).all().alias("allAtFloor"),
        )
        .filter(pl.col("nResults") >= minimum_results)
        .with_columns(
            (pl.col("logGeometricMean") > np.log10(WARNING_THRESHOLD)).alias(
                "overLimit"
            ),
            pl.col("collectionDate").dt.year().alias("year"),
            pl.col("collectionDate").dt.strftime("%Y-%m").alias("monthYear"),
        )
        .sort("beachName", "collectionDate")
    )


def exceedance_by_beach(daily: pl.DataFrame) -> pl.DataFrame:
    """The share of each beach's sampled days that went over the limit."""
    return (
        daily.group_by("beachName")
        .agg(
            pl.len().alias("days"),
            pl.col("overLimit").sum().alias("daysOverLimit"),
            pl.col("overLimit").mean().alias("share"),
        )
        .sort("share", descending=True)
    )


def exceedance_by_beach_and_year(daily: pl.DataFrame) -> pl.DataFrame:
    """The same share, season by season."""
    return (
        daily.group_by("beachName", "year")
        .agg(
            pl.len().alias("days"),
            pl.col("overLimit").sum().alias("daysOverLimit"),
            pl.col("overLimit").mean().alias("share"),
        )
        .sort("beachName", "year")
    )


def overdispersion(daily: pl.DataFrame) -> float:
    """Variance over mean of the days above the limit, per beach per season.

    A Poisson distribution has variance equal to its mean, so a ratio near 1
    would mean days over the limit arrive independently at a steady rate. A
    larger ratio means they cluster, which is what a wet week does.
    """
    per_season = daily.group_by("beachName", "year").agg(
        pl.col("overLimit").sum().alias("daysOverLimit")
    )
    return per_season["daysOverLimit"].var() / per_season["daysOverLimit"].mean()


def fit_beach_model(daily: pl.DataFrame):
    """Compare beaches on days when they were sampled together.

    The outcome is each day's log10 geometric mean with that day's city-wide
    average subtracted, which is what including a term for every date would do:
    a beach is compared only with the other beaches sampled the same day, so a
    wet week raises nobody's estimate. Each coefficient is a beach's average gap
    from the others, on the log10 scale, so 0.3 means about twice as high.

    Standard errors are clustered by calendar month (for example July 2019),
    because levels carry over from one day to the next and consecutive days are
    not independent trials. Partial months at the start and end of a season are
    kept as smaller clusters.

    Subtracting the daily average uses up information the count of rows does not
    know about, so the reported degrees of freedom are slightly optimistic. With
    96 clusters the effect on the intervals is small.
    """
    prepared = daily.with_columns(
        (
            pl.col("logGeometricMean")
            - pl.col("logGeometricMean").mean().over("collectionDate")
        ).alias("relativeToDay"),
        # Patsy needs names it can put in a formula.
        pl.col("beachName").str.replace_all(r"[^A-Za-z]", "").alias("beach"),
    )
    return smf.ols("relativeToDay ~ beach - 1", data=prepared.to_pandas()).fit(
        cov_type="cluster",
        cov_kwds={"groups": prepared["monthYear"].to_list()},
    )


def pairwise_differences(model, method: str = "holm") -> pl.DataFrame:
    """Every pair of beaches compared, corrected for making 45 comparisons.

    With ten beaches there are 45 pairs, and testing that many at the usual 5%
    level would produce a couple of false differences by chance alone. Holm's
    method raises the bar each test has to clear so that the chance of any false
    difference across the whole family stays near 5%.
    """
    names = list(model.params.index)
    rows = []
    for first in range(len(names)):
        for second in range(first + 1, len(names)):
            contrast = np.zeros(len(names))
            contrast[first], contrast[second] = 1.0, -1.0
            test = model.t_test(contrast)
            rows.append(
                {
                    "beachA": names[first].removeprefix("beach[").removesuffix("]"),
                    "beachB": names[second].removeprefix("beach[").removesuffix("]"),
                    "difference": float(np.squeeze(test.effect)),
                    "standardError": float(np.squeeze(test.sd)),
                    "pValue": float(np.squeeze(test.pvalue)),
                }
            )

    differences = pl.DataFrame(rows)
    corrected = multipletests(differences["pValue"].to_numpy(), method=method)[1]
    return differences.with_columns(
        pl.Series("pValueCorrected", corrected),
        (pl.Series("pValueCorrected", corrected) < 0.05).alias("differs"),
    ).sort("pValueCorrected")


def consecutive_day_pairs(daily: pl.DataFrame) -> pl.DataFrame:
    """Each beach-day paired with the day before, where they are consecutive.

    Days either side of a gap are not paired: advice carried over a three-day
    gap is not the process being described.
    """
    return (
        daily.with_columns(
            pl.col("logGeometricMean").shift(1).over("beachName").alias("previousMean"),
            pl.col("collectionDate").shift(1).over("beachName").alias("previousDate"),
            pl.col("overLimit").shift(1).over("beachName").alias("previousOverLimit"),
            pl.col("allAtFloor").shift(1).over("beachName").alias("previousAllAtFloor"),
        )
        .filter(
            (pl.col("collectionDate") - pl.col("previousDate")).dt.total_days() == 1
        )
        .drop_nulls("previousMean")
    )


def warning_agreement(pairs: pl.DataFrame) -> pl.DataFrame:
    """How often yesterday's result gives the right advice about today.

    Results take about a day from the laboratory, so a posting reflects the
    previous day's water. Treating yesterday's result as today's advice gives
    four outcomes, and this counts them. It depends only on which side of the
    limit each day fell, so the detection floor does not affect it.
    """
    outcomes = {
        "correct warning": (True, True),
        "correct all-clear": (False, False),
        "unneeded warning": (True, False),
        "missed warning": (False, True),
    }
    rows = [
        {
            "outcome": name,
            "days": pairs.filter(
                (pl.col("previousOverLimit") == yesterday)
                & (pl.col("overLimit") == today)
            ).height,
        }
        for name, (yesterday, today) in outcomes.items()
    ]
    return pl.DataFrame(rows).with_columns(
        (pl.col("days") / pl.col("days").sum()).alias("share")
    )


def day_to_day_correlation(pairs: pl.DataFrame) -> dict[str, float]:
    """How well one day's level predicts the next.

    Reported twice. About half of all samples sit at the detection limit, so
    many pairs have both days at the floor and agree perfectly by construction,
    which flatters the correlation without showing any predictive power. The
    second figure drops those pairs.
    """
    uncensored = pairs.filter(
        ~(pl.col("allAtFloor") & pl.col("previousAllAtFloor").fill_null(False))
    )
    return {
        "all pairs": pairs.select(pl.corr("logGeometricMean", "previousMean")).item(),
        "excluding pairs with both days at the floor": uncensored.select(
            pl.corr("logGeometricMean", "previousMean")
        ).item(),
        "pairs": pairs.height,
        "uncensored pairs": uncensored.height,
    }
