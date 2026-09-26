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
            # The month used to group days for the standard errors. The few
            # sampling days in late May and early September are counted with June
            # and August, so that no group is only a handful of days.
            (
                pl.col("collectionDate").dt.year().cast(pl.String)
                + "-"
                + pl.col("collectionDate")
                .dt.month()
                .clip(6, 8)
                .cast(pl.String)
                .str.zfill(2)
            ).alias("groupMonth"),
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
    """The same share, year by year."""
    return (
        daily.group_by("beachName", "year")
        .agg(
            pl.len().alias("days"),
            pl.col("overLimit").sum().alias("daysOverLimit"),
            pl.col("overLimit").mean().alias("share"),
        )
        .sort("beachName", "year")
    )


def _relative_to_day(daily: pl.DataFrame) -> pl.DataFrame:
    """Each beach-day's log10 geometric mean minus that day's city-wide average."""
    return daily.with_columns(
        (
            pl.col("logGeometricMean")
            - pl.col("logGeometricMean").mean().over("collectionDate")
        ).alias("relativeToDay"),
        # Patsy needs names it can put in a formula.
        pl.col("beachName").str.replace_all(r"[^A-Za-z]", "").alias("beach"),
    )


def fit_beach_model(daily: pl.DataFrame):
    """Compare beaches on days when they were sampled together.

    The outcome is each day's log10 geometric mean with that day's city-wide
    average subtracted, which is what including a term for every date would do:
    a beach is compared only with the other beaches sampled the same day, so a
    wet week raises nobody's estimate. Each coefficient is a beach's average gap
    from the others, on the log10 scale, so 0.3 means about twice as high.

    Standard errors are clustered by month (for example July 2019), because
    levels carry over from one day to the next and consecutive days are not
    independent trials. The partial months at each end of the season are merged
    into June and August, giving 60 groups rather than 96.

    Subtracting the daily average uses up information the count of rows does not
    know about, so the reported degrees of freedom are slightly optimistic. With
    60 clusters the effect on the intervals is small.
    """
    prepared = _relative_to_day(daily)
    return smf.ols("relativeToDay ~ beach - 1", data=prepared.to_pandas()).fit(
        cov_type="cluster",
        cov_kwds={"groups": prepared["groupMonth"].to_list()},
    )


def standard_error_inflation(daily: pl.DataFrame) -> pl.DataFrame:
    """How much wider each beach's standard error is when days are grouped by month.

    The same model is fitted twice: once treating every beach-day as independent,
    and once treating days in the same calendar month as related. The estimates
    are identical; only the standard errors differ. A ratio near 1 would mean
    consecutive days carry independent information and the grouping changes
    nothing. A ratio of 2 means the intervals are twice as wide, and the data
    hold about as much information as a quarter as many independent days.
    """
    prepared = _relative_to_day(daily)
    independent = smf.ols("relativeToDay ~ beach - 1", data=prepared.to_pandas()).fit()
    grouped = fit_beach_model(daily)
    return pl.DataFrame(
        {
            "beach": [
                name.removeprefix("beach[").removesuffix("]")
                for name in grouped.params.index
            ],
            "standardErrorIndependent": independent.bse.to_numpy(),
            "standardErrorByMonth": grouped.bse.to_numpy(),
        }
    ).with_columns(
        (pl.col("standardErrorByMonth") / pl.col("standardErrorIndependent")).alias(
            "ratio"
        )
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
