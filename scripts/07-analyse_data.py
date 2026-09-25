#### Preamble ####
# Purpose: Runs the paper's analysis on the cleaned City of Toronto data, using
# the same functions checked against the simulated data in
# `scripts/06-validate_on_simulated_data.py`. Answers the two questions in
# `other/notes/analysis_plan.md`: whether some beaches go over the limit more
# often than others, and how well one day's result predicts the next. Saves the
# tables to `other/results/` and the figure of beach estimates to `paper/figures/`.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy`, `statsmodels` and `matplotlib` must be installed
# - Run `uv run scripts/03-clean_data.py` first
# - Run from the project root: uv run scripts/07-analyse_data.py


#### Workspace setup ####
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.ticker import FixedLocator, NullLocator

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
FIGURE_DIR = Path("paper/figures")

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

# The year-by-year spread of each beach's share, which says whether the
# ranking is a property of the beach or of a few unusual summers.
year_spread = (
    by_year.group_by("beachName")
    .agg(
        pl.col("share").min().alias("lowestYear"),
        pl.col("share").max().alias("highestYear"),
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

# Whether the pairwise results depend on how days are grouped for the standard
# errors. The partial months at each end of the season (late May, early
# September) make small groups; here they are merged into June and August.
merged_months = daily.with_columns(
    (
        pl.col("collectionDate").dt.year().cast(pl.String)
        + "-"
        + pl.col("collectionDate").dt.month().clip(6, 8).cast(pl.String).str.zfill(2)
    ).alias("monthYear")
)
differences_merged = pairwise_differences(fit_beach_model(merged_months))
grouping_check = differences.select(
    "beachA",
    "beachB",
    "difference",
    pl.col("pValueCorrected").alias("pValueCalendarMonths"),
    pl.col("differs").alias("differsCalendarMonths"),
).join(
    differences_merged.select(
        "beachA",
        "beachB",
        pl.col("pValueCorrected").alias("pValueMergedMonths"),
        pl.col("differs").alias("differsMergedMonths"),
    ),
    on=["beachA", "beachB"],
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

print("\nLowest and highest year for each beach")
show(
    year_spread.with_columns(
        pl.col("share").round(3),
        pl.col("lowestYear").round(3),
        pl.col("highestYear").round(3),
    )
)

print("\nBefore and from 2018, when the reporting ceiling appeared")
show(halves.with_columns(pl.col("before2018").round(3), pl.col("from2018").round(3)))

print(
    f"\nDays over the limit per beach per year vary {clustering:.1f} times as much as"
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

print(
    f"\nGrouping partial months with their neighbours ({daily['monthYear'].n_unique()}"
    f" groups become {merged_months['monthYear'].n_unique()}):"
    f" {grouping_check['differsMergedMonths'].sum()} pairs differ instead of"
    f" {grouping_check['differsCalendarMonths'].sum()}. Pairs that change:"
)
show(
    grouping_check.filter(
        pl.col("differsCalendarMonths") != pl.col("differsMergedMonths")
    ).with_columns(
        pl.col("difference").round(3),
        pl.col("pValueCalendarMonths").round(3),
        pl.col("pValueMergedMonths").round(3),
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
grouping_check.write_csv(RESULTS_DIR / "beach-pairwise-grouping-check.csv")
agreement.write_csv(RESULTS_DIR / "warning-agreement.csv")
print(f"\nSaved the tables to {RESULTS_DIR}")


#### Figure: each beach against the others sampled the same day ####
# The model's estimates as fold differences, 10 to the power of the log10 gap,
# with 95% confidence intervals from the month-clustered standard errors.
# Colours and text styles match `scripts/05-exploratory_data_analysis.py`.
DATA_COLOUR = "#2a78d6"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOUR = "#e6e5e1"
Z_95 = 1.96

# The model uses names stripped of spaces and punctuation; map them back.
display_names = {
    name.replace(" ", "").replace("'", ""): name
    for name in daily["beachName"].unique().to_list()
}
fold = (
    coefficients.with_columns(
        pl.col("beach").replace_strict(display_names).alias("beachName"),
        (10 ** pl.col("estimate")).alias("fold"),
        (10 ** (pl.col("estimate") - Z_95 * pl.col("standardError"))).alias("low"),
        (10 ** (pl.col("estimate") + Z_95 * pl.col("standardError"))).alias("high"),
    )
    # Cleanest at the bottom, so the dirtiest beach reads first.
    .sort("estimate")
)

plt.rcParams.update(
    {
        "figure.dpi": 200,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": GRID_COLOUR,
    }
)
figure, axis = plt.subplots(figsize=(8, 4.2))
rows = np.arange(fold.height)
axis.hlines(rows, fold["low"], fold["high"], color=DATA_COLOUR, linewidth=2)
# Short caps mark where each interval ends, since judging overlap is the point.
for end in ("low", "high"):
    axis.vlines(fold[end], rows - 0.15, rows + 0.15, color=DATA_COLOUR, linewidth=1.5)
axis.scatter(fold["fold"], rows, s=36, color=DATA_COLOUR, zorder=3)
axis.axvline(1, color=TEXT_PRIMARY, linewidth=1, linestyle=(0, (6, 4)), zorder=1)
# Values in a column right of the plot, as in the beach-day figure, so that no
# label collides with the line at 1.
for row, value in enumerate(fold["fold"]):
    axis.text(
        1.02,
        row,
        f"{value:.2f}×",
        transform=axis.get_yaxis_transform(),
        va="center",
        fontsize=9,
        color=TEXT_SECONDARY,
    )

# A log scale, so that half as high and twice as high sit the same distance
# from the line at 1.
axis.set_xscale("log")
ticks = [0.6, 0.8, 1, 1.25, 1.5, 2, 2.5]
axis.xaxis.set_major_locator(FixedLocator(ticks))
axis.xaxis.set_minor_locator(NullLocator())
axis.set_xticklabels([f"{tick:g}×" for tick in ticks])
axis.set_xlim(0.6, 2.8)
axis.set_yticks(rows)
axis.set_yticklabels(fold["beachName"], fontsize=10, color=TEXT_PRIMARY)
axis.tick_params(axis="y", length=0)
axis.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)
axis.grid(axis="x", color=GRID_COLOUR, linewidth=0.5)
axis.set_axisbelow(True)
axis.set_xlabel(
    "E. coli relative to the average beach sampled the same day (log scale)",
    fontsize=10,
    color=TEXT_SECONDARY,
)
figure.tight_layout()
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
figure.savefig(FIGURE_DIR / "beach-estimates.png", bbox_inches="tight")
print(f"Saved {FIGURE_DIR / 'beach-estimates.png'}")
