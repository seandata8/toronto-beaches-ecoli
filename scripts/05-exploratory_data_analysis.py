#### Preamble ####
# Purpose: Draws the two figures that show the whole dataset: every published
# result over time, including the one that cleaning removes, and how high the
# results get at each beach.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy` and `matplotlib` must be installed
# - Run `uv run scripts/02-download_data.py` first
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
FIGURE_DIR = Path("other/explore/figures")

WARNING_THRESHOLD = 100

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
# Results over the threshold, which take the second slot of the same palette.
ABOVE_THRESHOLD_COLOUR = "#eb6834"
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


#### Shared axis formatting ####
# The x axis is log10 of the count, labelled with the counts themselves.
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


#### Summary figure: results by order of magnitude, by beach ####
# Every result except the one removed as an error, counted in bands of ten:
# 1 to 10, 11 to 100, and so on. Bands rather than narrow bars because the
# threshold sits exactly on a band edge, so the share of a beach's results above
# 100 is the last two bars of its panel.
# Sites 60W and GP6 are left out, as in the analysis: they cover 2026 only and sit
# 14 to 16 km from the beaches they are listed under.
summary_results = rest.filter(~pl.col("siteName").is_in(["60W", "GP6"]))

# Four bands, not five: only four results in twenty years passed 10,000, so a
# separate band for them would be an empty column in every panel.
BAND_EDGES = [1, 2, 3]
BAND_LABELS = ["1–10", "11–100", "101–\n1,000", "over\n1,000"]

banded = (
    summary_results.with_columns(
        pl.col("logEColi")
        .cut(BAND_EDGES, labels=[str(band) for band in range(len(BAND_LABELS))])
        .cast(pl.Int8)
        .alias("band")
    )
    .group_by("beachName", "band")
    .agg(pl.len().alias("results"))
)

summary_order = (
    banded.with_columns(
        (pl.col("results") * (pl.col("band") >= 2)).alias("aboveThreshold")
    )
    .group_by("beachName")
    .agg((pl.col("aboveThreshold").sum() / pl.col("results").sum()).alias("share"))
    .sort("share", descending=True)["beachName"]
    .to_list()
)

figure, axes = plt.subplots(2, 5, figsize=(10, 6.6), sharex=True, sharey=True)
for axis, beach in zip(axes.flat, summary_order):
    counts = (
        banded.filter(pl.col("beachName") == beach)
        .sort("band")
        .select("band", "results")
    )
    heights = [
        counts.filter(pl.col("band") == band)["results"].sum()
        for band in range(len(BAND_LABELS))
    ]
    total = sum(heights)
    # Bands above the threshold take their own hue, so a panel can be read
    # without tracing back to the dashed line.
    band_colours = [
        ABOVE_THRESHOLD_COLOUR if band >= 2 else DATA_COLOUR
        for band in range(len(BAND_LABELS))
    ]
    bars = axis.bar(range(len(BAND_LABELS)), heights, color=band_colours, width=0.72)

    # The share of results in each band, so a reader can compare beaches with
    # different numbers of samples without doing the arithmetic.
    for bar, height in zip(bars, heights):
        if height == 0:
            continue
        axis.annotate(
            f"{height / total:.0%}" if height / total >= 0.005 else "<1%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            fontsize=7,
            color=TEXT_SECONDARY,
        )

    axis.set_title(fill(beach, width=18), fontsize=9.5, color=TEXT_PRIMARY, loc="left")
    axis.set_xticks(range(len(BAND_LABELS)))
    axis.set_xticklabels(BAND_LABELS, fontsize=7.5)
    axis.grid(axis="y", color=GRID_COLOUR, linewidth=0.5)
    axis.set_axisbelow(True)
    # The threshold falls on the edge between the second and third band.
    axis.axvline(1.5, color=TEXT_PRIMARY, linewidth=1, linestyle=(0, (6, 4)), zorder=3)

figure.text(
    0.008,
    1.0,
    "How high the results get, by beach",
    ha="left",
    va="top",
    fontsize=13,
    color=TEXT_PRIMARY,
)
figure.text(
    0.008,
    0.955,
    fill(
        f"Every result the City has published ({summary_results.height:,}), with each bar"
        " labelled by its share of that beach's results. The reading of 6,191,768 removed as an"
        " error is left out, as are two sites added in 2026 that sit far from the beaches they"
        " are listed under. The orange bars, right of the dashed line, are the results above 100"
        " E. coli per 100 mL, the limit the City of Toronto sets for safe swimming. Panels run"
        " from the beach with the largest share above that limit to the smallest. Each bar counts"
        " single samples rather than days: a beach is judged on the average of its five or six"
        " samples, and by that measure Marie Curtis Park East Beach was over the limit on 658 of"
        " its 1,927 sampled days, or 34%, against the 36% of its samples shown here.",
        width=CAPTION_WIDTH,
    ),
    ha="left",
    va="top",
    fontsize=9.5,
    color=TEXT_SECONDARY,
)
figure.supylabel("Number of results", fontsize=10, color=TEXT_SECONDARY)
figure.supxlabel("E. coli per 100 mL", fontsize=10, color=TEXT_SECONDARY)
figure.tight_layout(rect=(0.004, 0, 1, 0.78))
figure.savefig(FIGURE_DIR / "results-by-magnitude.png", bbox_inches="tight")

print(f"Saved two figures to {FIGURE_DIR}")
print(f"Results plotted: {rest.height:,}")
