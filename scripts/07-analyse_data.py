#### Preamble ####
# Purpose: Runs the paper's analysis on the cleaned City of Toronto data, using
# the same functions checked against the simulated data in
# `scripts/06-validate_on_simulated_data.py`. Answers the two questions in
# `other/notes/analysis_plan.md`: whether some beaches go over the limit more
# often than others, and how well one day's result predicts the next.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy` and `statsmodels` must be installed
# - Run `uv run scripts/03-clean_data.py` first
# - Run from the project root: uv run scripts/07-analyse_data.py


#### Workspace setup ####
from pathlib import Path

import polars as pl

from toronto_beaches_ecoli.analysis import (
    consecutive_day_pairs,
    daily_geometric_means,
    day_to_day_correlation,
    exceedance_by_beach,
    exceedance_by_beach_and_year,
    fit_beach_model,
    overdispersion,
    pairwise_differences,
    warning_agreement,
)

ANALYSIS_DATA_PATH = "data/02-analysis_data/analysis_data.csv"
RESULTS_DIR = Path("other/results")

analysis_data = pl.read_csv(ANALYSIS_DATA_PATH, try_parse_dates=True)
daily = daily_geometric_means(analysis_data)


#### Question 1: do some beaches go over the limit more often? ####
shares = exceedance_by_beach(daily)
by_year = exceedance_by_beach_and_year(daily)
clustering = overdispersion(daily)

model = fit_beach_model(daily)
coefficients = pl.DataFrame(
    {
        "beach": [
            name.removeprefix("beach[").removesuffix("]") for name in model.params.index
        ],
        "estimate": model.params.to_numpy(),
        "standardError": model.bse.to_numpy(),
    }
).sort("estimate", descending=True)

differences = pairwise_differences(model)

# The season-by-season spread of each beach's share, which says whether the
# ranking is a property of the beach or of a few unusual summers.
season_spread = (
    by_year.group_by("beachName")
    .agg(
        pl.col("share").min().alias("lowestSeason"),
        pl.col("share").max().alias("highestSeason"),
    )
    .join(shares.select("beachName", "share"), on="beachName")
    .sort("share", descending=True)
)

# Whether the ranking holds in both halves of the record. The ceiling arrived in
# 2018, so if it were driving the result the two halves would disagree.
halves = (
    daily.with_columns((pl.col("year") >= 2018).alias("fromCeiling"))
    .group_by("beachName", "fromCeiling")
    .agg(pl.col("overLimit").mean().alias("share"))
    .pivot(on="fromCeiling", index="beachName", values="share")
    .rename({"false": "before2018", "true": "from2018"})
    .sort("before2018", descending=True)
)


#### Question 2: how well does one day predict the next? ####
pairs = consecutive_day_pairs(daily)
agreement = warning_agreement(pairs)
correlation = day_to_day_correlation(pairs)

# Of the days that were actually over the limit, how many did yesterday's result
# catch? And of the warnings yesterday's result would have posted, how many were
# needed? These are the two numbers a swimmer cares about.
over_today = agreement.filter(
    pl.col("outcome").is_in(["correct warning", "missed warning"])
)["days"].sum()
caught = agreement.filter(pl.col("outcome") == "correct warning")["days"].item()
posted = agreement.filter(
    pl.col("outcome").is_in(["correct warning", "unneeded warning"])
)["days"].sum()


#### Report ####
def show(frame: pl.DataFrame) -> None:
    with pl.Config(tbl_rows=-1, tbl_hide_dataframe_shape=True, fmt_str_lengths=40):
        print(frame)


print(f"Beach-days analysed: {daily.height:,}\n")

print("Question 1: share of sampled days over 100 E. coli per 100 mL")
show(shares.with_columns(pl.col("share").round(3)))

print("\nLowest and highest season for each beach")
show(
    season_spread.with_columns(
        pl.col("share").round(3),
        pl.col("lowestSeason").round(3),
        pl.col("highestSeason").round(3),
    )
)

print("\nBefore and from 2018, when the reporting ceiling appeared")
show(halves.with_columns(pl.col("before2018").round(3), pl.col("from2018").round(3)))

print(
    f"\nDays over the limit per beach per season vary {clustering:.1f} times as much as"
    "\na Poisson distribution allows, so they cluster rather than arriving steadily."
)

print("\nModel: how far each beach sits above or below the others sampled the same day")
print("(log10 scale, so 0.30 means about twice as high)")
show(
    coefficients.with_columns(
        pl.col("estimate").round(3), pl.col("standardError").round(3)
    )
)

separated = differences.filter(pl.col("differs")).height
print(
    f"\nOf the {differences.height} pairs of beaches, {separated} differ after correcting"
    " for multiple comparisons."
)
print("\nThe ten largest differences between beaches")
show(
    differences.head(10).with_columns(
        pl.col("difference").round(3),
        pl.col("standardError").round(3),
        pl.col("pValueCorrected").round(4),
    )
)

print("\nPairs that cannot be told apart")
show(
    differences.filter(~pl.col("differs")).with_columns(
        pl.col("difference").round(3), pl.col("pValueCorrected").round(3)
    )
)

print("\n\nQuestion 2: treating yesterday's result as today's advice")
show(agreement.with_columns(pl.col("share").round(3)))
print(f"\nConsecutive-day pairs: {correlation['pairs']:,}")
print(f"Days actually over the limit: {over_today:,}")
print(f"  of which yesterday's result caught: {caught:,} ({caught / over_today:.0%})")
print(f"Warnings yesterday's result would post: {posted:,}")
print(f"  of which were needed: {caught:,} ({caught / posted:.0%})")
print(
    f"\nCorrelation between one day and the next: {correlation['all pairs']:.3f}"
    f"\n  excluding pairs with both days at the floor: "
    f"{correlation['excluding pairs with both days at the floor']:.3f}"
    f" ({correlation['uncensored pairs']:,} pairs)"
)


#### Save the tables the paper uses ####
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
shares.write_csv(RESULTS_DIR / "exceedance-by-beach.csv")
by_year.write_csv(RESULTS_DIR / "exceedance-by-beach-and-year.csv")
coefficients.write_csv(RESULTS_DIR / "beach-model-coefficients.csv")
differences.write_csv(RESULTS_DIR / "beach-pairwise-differences.csv")
agreement.write_csv(RESULTS_DIR / "warning-agreement.csv")
print(f"\nSaved the tables to {RESULTS_DIR}")
