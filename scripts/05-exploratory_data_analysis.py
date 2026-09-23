#### Preamble ####
# Purpose: Draws the two graphs that show the whole dataset: every sample result,
# and every beach-day geometric mean. Written against the simulated data so that
# the plotting code is ready before the real data is cleaned; change
# DATA_PATH to the analysis data once `scripts/03-clean_data.py` exists.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy` and `matplotlib` must be installed
# - Run `uv run scripts/00-simulate_data.py` first
# - Run from the project root: uv run scripts/05-exploratory_data_analysis.py


#### Workspace setup ####
import math
from pathlib import Path
from textwrap import fill

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.ticker import FixedLocator, FuncFormatter

RAW_DATA_PATH = "data/01-raw_data/raw_data.csv"
DATA_PATH = "data/00-simulated_data/simulated_data.csv"
FIGURE_DIR = Path("other/explore/figures")

WARNING_THRESHOLD = 100
DETECTION_LIMIT = 10
MINIMUM_RESULTS = 4

# Sampling is daily and results are reported in steps of ten, so points land on a
# grid and pile up. Spreading them sideways by a few days makes the pile-ups
# countable; the y position, which carries the measurement, is never moved.
RAW_JITTER_DAYS = 60

# Characters per caption line, set so that a caption fits the figure width.
CAPTION_WIDTH = 118

rng = np.random.default_rng(853)

# Colours: one series, so one hue. The threshold is the only other mark that
# needs to stand out, and text stays in ink rather than taking the series colour.
DATA_COLOUR = "#2a78d6"
THRESHOLD_COLOUR = "#e34948"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOUR = "#e6e5e1"

plt.rcParams.update(
    {
        "figure.dpi": 200,
        "font.size": 10,
        "text.color": TEXT_PRIMARY,
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.edgecolor": GRID_COLOUR,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "xtick.labelcolor": TEXT_SECONDARY,
        "ytick.labelcolor": TEXT_SECONDARY,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


#### Read data ####
results = (
    pl.read_csv(DATA_PATH, try_parse_dates=True)
    .drop_nulls("eColi")
    .with_columns(pl.col("eColi").log10().alias("logEColi"))
)

# The unit the analysis uses: one geometric mean per beach per day, computed only
# when at least four results are available.
daily_means = (
    results.group_by("beachName", "collectionDate")
    .agg(
        pl.col("logEColi").mean().alias("logGeometricMean"),
        pl.len().alias("nResults"),
    )
    .filter(pl.col("nResults") >= MINIMUM_RESULTS)
)

# Beaches are ordered by how often they exceeded the threshold, so both graphs
# read top to bottom as worst to cleanest.
beach_order = (
    daily_means.group_by("beachName")
    .agg(
        (pl.col("logGeometricMean") > np.log10(WARNING_THRESHOLD))
        .mean()
        .alias("exceedanceShare")
    )
    .sort("exceedanceShare", descending=True)["beachName"]
    .to_list()
)


#### Shared axis formatting ####
# The x axis is log10 of the count, labelled with the counts themselves.
TICK_VALUES = [10, 100, 1_000, 10_000]
count_formatter = FuncFormatter(lambda value, _: f"{10**value:,.0f}")


def to_significant_figures(value: float, digits: int = 2) -> float:
    """Round to a number of significant figures, e.g. 61,917 to 62,000.

    Formatting alone cannot do this: the "g" format switches to scientific
    notation for large numbers, and thousands separators do not apply to it.
    """
    if value == 0:
        return 0.0
    magnitude = math.floor(math.log10(abs(value)))
    return round(value, -(magnitude - digits + 1))


def style_count_axis(axis, ticks: list[int] = TICK_VALUES) -> None:
    """Label a log10 axis with counts, and mark the threshold.

    The small panels take fewer ticks than the full-width figures, because at
    this type size "1,000" and "10,000" would otherwise run together.
    """
    axis.xaxis.set_major_locator(FixedLocator(np.log10(ticks)))
    axis.xaxis.set_major_formatter(count_formatter)
    axis.axvline(
        np.log10(WARNING_THRESHOLD),
        color=THRESHOLD_COLOUR,
        linewidth=1,
        zorder=3,
    )


#### Graph 0: every raw result, including the one that cleaning removes ####
# Read before any cleaning, so that the reader sees the reading of 6,191,768 that
# the analysis drops, and can judge the decision.
raw_results = (
    pl.read_csv(RAW_DATA_PATH, try_parse_dates=True)
    .with_columns(pl.col("eColi").cast(pl.Float64, strict=False))
    .drop_nulls("eColi")
    .with_columns(
        pl.col("eColi").clip(lower_bound=1).log10().alias("logEColi"),
        pl.col("collectionDate").cast(pl.Date),
    )
)
outlier = raw_results.filter(pl.col("eColi") == pl.col("eColi").max())
rest = raw_results.filter(pl.col("eColi") < pl.col("eColi").max())

jittered_dates = mdates.date2num(rest["collectionDate"].to_numpy()) + rng.uniform(
    -RAW_JITTER_DAYS, RAW_JITTER_DAYS, size=rest.height
)

figure, axis = plt.subplots(figsize=(9, 5.6))
axis.scatter(
    jittered_dates,
    rest["logEColi"],
    s=20,
    alpha=0.2,
    color=DATA_COLOUR,
    linewidths=0,
    rasterized=True,
)
# The removed reading is drawn in the same blue as every other sample, because it
# is one. A red ring marks it instead, so the colour still means "a measurement"
# and the red means "the thing being pointed at".
axis.scatter(
    outlier["collectionDate"],
    outlier["logEColi"],
    s=20,
    color=DATA_COLOUR,
    linewidths=0,
    zorder=4,
)
axis.scatter(
    outlier["collectionDate"],
    outlier["logEColi"],
    s=190,
    facecolors="none",
    edgecolors=THRESHOLD_COLOUR,
    linewidths=1,
    zorder=5,
)
# The line is black and dashed rather than a solid colour: a solid line crossing
# columns of dots appears to bend where it meets them, and the dashes break that up.
axis.axhline(
    np.log10(WARNING_THRESHOLD),
    color=TEXT_PRIMARY,
    linewidth=1,
    linestyle=(0, (6, 4)),
    zorder=3,
    label=f"Swimming warning threshold, {WARNING_THRESHOLD} per 100 mL",
)

outlier_value = int(outlier["eColi"].item())
outlier_date = outlier["collectionDate"].item()
# The case for removal is not that the reading is high, but that nothing else in
# twenty years comes near it: the next highest is smaller by a factor of 390.
next_highest = rest["eColi"].max()
axis.annotate(
    f"{outlier_value:,} per 100 mL at {outlier['beachName'].item()},\n"
    f"{outlier_date:%-d %B %Y}: about "
    f"{to_significant_figures(outlier_value / next_highest):,.0f} times the next\n"
    f"highest reading ever recorded ({next_highest:,.0f}), and removed as an error",
    xy=(outlier_date, outlier["logEColi"].item()),
    xytext=(16, -34),
    textcoords="offset points",
    ha="left",
    fontsize=7,
    color=THRESHOLD_COLOUR,
    arrowprops={
        "arrowstyle": "->",
        "color": THRESHOLD_COLOUR,
        "linewidth": 0.8,
        # Stop the arrow short of the ring rather than running into it.
        "shrinkB": 10,
    },
)
axis.legend(
    loc="upper right",
    frameon=False,
    fontsize=9,
    handlelength=3,
    labelcolor=TEXT_SECONDARY,
)

axis.xaxis_date()
axis.yaxis.set_major_locator(FixedLocator(np.log10([10, 1_000, 100_000, 10_000_000])))
axis.yaxis.set_major_formatter(count_formatter)
axis.grid(axis="y", color=GRID_COLOUR, linewidth=0.5)
axis.set_axisbelow(True)
axis.set_ylabel("E. coli per 100 mL (log scale)", fontsize=10, color=TEXT_SECONDARY)

figure.text(
    0.008,
    1.0,
    "Every result the City has published, 2007 to 2026",
    ha="left",
    va="top",
    fontsize=13,
    color=TEXT_PRIMARY,
)
figure.text(
    0.008,
    0.955,
    fill(
        f"One point is one water sample ({raw_results.height:,} in total), before any cleaning."
        " Points are spread sideways within each year so that they can be better visualized;"
        " the E. coli count itself is never moved. The majority of the results are reported in"
        " multiples of 10, which is why the low readings fall into separate rows. The laboratory"
        " reports no results as zero and it was assumed that 'no colonies detected' is reported"
        " at 10. From 2018 onward, many values are reported as 1,000 and these were assumed to be"
        " measurements that were >=1000. The dashed line marks 100 per 100 mL, the level at which"
        " the City posts a swimming warning. The ringed point is the only reading the analysis"
        " removes.",
        width=CAPTION_WIDTH,
    ),
    ha="left",
    va="top",
    fontsize=9.5,
    color=TEXT_SECONDARY,
)
figure.tight_layout(rect=(0, 0, 1, 0.74))
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
figure.savefig(FIGURE_DIR / "all-raw-results.png", bbox_inches="tight")


#### Graph 1: every sample result ####
# A histogram rather than a density: results are reported in steps of ten, so the
# bars are the data rather than a smoothing of it, and the reporting floor stays
# visible as the single tall bar it is.
bins = np.arange(0.95, results["logEColi"].max() + 0.1, 0.1)

figure, axes = plt.subplots(2, 5, figsize=(9, 5.0), sharex=True, sharey=True)
for axis, beach in zip(axes.flat, beach_order):
    beach_results = results.filter(pl.col("beachName") == beach)
    axis.hist(beach_results["logEColi"], bins=bins, color=DATA_COLOUR, linewidth=0)
    style_count_axis(axis, ticks=[10, 100, 1_000])
    # Names are wrapped rather than shortened, so that a panel title never runs
    # into the panel beside it.
    axis.set_title(
        fill(beach, width=18),
        fontsize=9.5,
        color=TEXT_PRIMARY,
        loc="left",
        pad=4,
    )
    axis.grid(axis="y", color=GRID_COLOUR, linewidth=0.5)
    axis.set_axisbelow(True)
    axis.set_xlim(bins[0], bins[-1])

figure.text(
    0.008,
    1.0,
    "Every E. coli result, by beach",
    ha="left",
    va="top",
    fontsize=13,
    color=TEXT_PRIMARY,
)
figure.text(
    0.008,
    0.955,
    fill(
        "Each bar counts the results in one narrow band of the log scale. Half of all results are"
        f" reported at {DETECTION_LIMIT}, the lowest the laboratory can measure, which is the tall"
        f" bar at the left of every panel. The red line marks {WARNING_THRESHOLD} per 100 mL, above"
        " which a beach is posted.",
        width=CAPTION_WIDTH,
    ),
    ha="left",
    va="top",
    fontsize=9.5,
    color=TEXT_SECONDARY,
)
figure.supxlabel("E. coli per 100 mL (log scale)", fontsize=10, color=TEXT_SECONDARY)
figure.supylabel("Number of results", fontsize=10, color=TEXT_SECONDARY)
figure.tight_layout(rect=(0.004, 0, 1, 0.86))

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
figure.savefig(FIGURE_DIR / "all-results-by-beach.png", bbox_inches="tight")


#### Graph 2: every beach-day geometric mean ####
# One point per beach-day, spread vertically at random so that overlapping points
# stay countable. This plots the actual unit the analysis uses.
threshold = np.log10(WARNING_THRESHOLD)

figure, axis = plt.subplots(figsize=(9, 5.0))
for row, beach in enumerate(reversed(beach_order)):
    beach_means = daily_means.filter(pl.col("beachName") == beach)[
        "logGeometricMean"
    ].to_numpy()
    height = row + rng.uniform(-0.32, 0.32, size=beach_means.size)
    exceeds = beach_means > threshold
    # Days over the threshold are the subject of the paper, so they carry their
    # own colour. Position relative to the line says the same thing, so the
    # colour is not doing the work alone.
    for selected, colour, opacity in (
        (~exceeds, DATA_COLOUR, 0.10),
        (exceeds, THRESHOLD_COLOUR, 0.30),
    ):
        axis.scatter(
            beach_means[selected],
            height[selected],
            s=1.5,
            alpha=opacity,
            color=colour,
            linewidths=0,
            rasterized=True,
        )
    # The share of days over the threshold, labelled directly rather than left
    # for the reader to judge from the density of the points.
    axis.text(
        1.005,
        row,
        f"{exceeds.mean():.0%}",
        transform=axis.get_yaxis_transform(),
        va="center",
        fontsize=10,
        color=THRESHOLD_COLOUR,
    )

style_count_axis(axis)
axis.set_yticks(range(len(beach_order)))
axis.set_yticklabels(list(reversed(beach_order)), fontsize=10, color=TEXT_PRIMARY)
axis.set_ylim(-0.7, len(beach_order) - 0.3)
axis.grid(axis="x", color=GRID_COLOUR, linewidth=0.5)
axis.set_axisbelow(True)
axis.tick_params(axis="y", length=0)
axis.text(
    1.005,
    len(beach_order) - 0.35,
    "Share of\ndays over",
    transform=axis.get_yaxis_transform(),
    va="bottom",
    fontsize=9,
    color=TEXT_SECONDARY,
)

figure.text(
    0.008,
    1.0,
    "Every beach-day, by beach",
    ha="left",
    va="top",
    fontsize=13,
    color=TEXT_PRIMARY,
)
figure.text(
    0.008,
    0.955,
    fill(
        "One point is the geometric mean of a beach's samples on one day, spread vertically so that"
        f" points can be counted ({daily_means.height:,} in total). Red points are the days above"
        f" {WARNING_THRESHOLD} per 100 mL, the threshold for posting a beach.",
        width=CAPTION_WIDTH,
    ),
    ha="left",
    va="top",
    fontsize=9.5,
    color=TEXT_SECONDARY,
)
axis.set_xlabel("E. coli per 100 mL (log scale)", fontsize=10, color=TEXT_SECONDARY)
figure.tight_layout(rect=(0, 0, 1, 0.86))

figure.savefig(FIGURE_DIR / "all-beach-days.png", bbox_inches="tight")

print(f"Saved two figures to {FIGURE_DIR}")
print(f"Results plotted: {results.height:,}")
print(f"Beach-days plotted: {daily_means.height:,}")
