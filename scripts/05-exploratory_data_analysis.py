#### Preamble ####
# Purpose: Draws the four figures that show the whole dataset: a map of the
# sampling sites; every published result over time, including the one that
# cleaning removes; how high the results get at each beach; and every beach-day,
# which is the unit the analysis uses. The figures are saved to `paper/figures/`
# and the paper reads the saved images. Titles and captions are in the paper, not
# the images; the numbers the captions quote are printed at the end.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy`, `matplotlib` and `contextily` must be installed
# - Run `uv run scripts/02-download_data.py` and `scripts/03-clean_data.py` first
# - Needs an internet connection: the map's basemap tiles are downloaded
# - Run from the project root: uv run scripts/05-exploratory_data_analysis.py


#### Workspace setup ####
import math
from pathlib import Path
from textwrap import fill

import contextily as cx
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.ticker import FixedLocator, FuncFormatter

RAW_DATA_PATH = "data/01-raw_data/raw_data.csv"
ANALYSIS_DATA_PATH = "data/02-analysis_data/analysis_data.csv"
FIGURE_DIR = Path("paper/figures")

WARNING_THRESHOLD = 100
DETECTION_LIMIT = 10

# The daily geometric mean needs at least four results: four, not five, so that
# Sunnyside's four sites are included.
MINIMUM_RESULTS = 4

# Sampling is daily and results are reported in steps of ten, so points land on a
# grid and pile up. Spreading them sideways by a few days makes the pile-ups
# countable; the y position, which carries the measurement, is never moved.
RAW_JITTER_DAYS = 60

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


#### Map: where the sampling sites are ####
# The raw data, so the two sites that cleaning leaves out can be shown: both are
# listed under beaches 14 to 16 km away.
DROPPED_SITES = ["60W", "GP6"]
# Offsets in points and horizontal alignment for their labels, set above each dot
DROPPED_LABEL_PLACES = {"60W": ((0, 10), "center"), "GP6": ((8, 10), "right")}

# Label offsets in points (x, y), chosen by hand so names don't overlap
LABEL_OFFSETS = {
    "Marie Curtis Park East Beach": (12, 0),
    "Sunnyside Beach": (0, 12),
    "Hanlan's Point Beach": (-10, -12),
    "Gibraltar Point Beach": (0, -24),
    "Centre Island Beach": (10, -14),
    "Ward's Island Beach": (14, -6),
    "Cherry Beach": (0, 12),
    "Woodbine Beaches": (-10, -14),
    "Kew Balmy Beach": (10, -12),
    "Bluffer's Beach Park": (-10, 0),
}
# Long names split over two lines so they stay inside the map
LABEL_TEXT = {"Marie Curtis Park East Beach": "Marie Curtis Park\nEast Beach"}

# One row per site, with longitude and latitude taken from the GeoJSON point
sites = (
    pl.read_csv(RAW_DATA_PATH)
    .with_columns(
        lon=pl.col("geometry")
        .str.json_path_match("$.coordinates[0][0]")
        .cast(pl.Float64),
        lat=pl.col("geometry")
        .str.json_path_match("$.coordinates[0][1]")
        .cast(pl.Float64),
    )
    .select("beachName", "siteName", "lon", "lat")
    .unique()
    # unique returns rows in no fixed order; sorting fixes the drawing order
    .sort("beachName", "siteName")
)

# Web Mercator (EPSG:3857) coordinates in metres, the projection of web map tiles
EARTH_RADIUS = 6_378_137
sites = sites.with_columns(
    x=np.radians(pl.col("lon")) * EARTH_RADIUS,
    y=(np.pi / 4 + np.radians(pl.col("lat")) / 2).tan().log() * EARTH_RADIUS,
)

kept_sites = sites.filter(~pl.col("siteName").is_in(DROPPED_SITES))
dropped_sites = sites.filter(pl.col("siteName").is_in(DROPPED_SITES))
beach_centres = kept_sites.group_by("beachName").agg(
    pl.col("x").mean(), pl.col("y").mean()
)

figure, axis = plt.subplots(figsize=(11, 6))
axis.scatter(
    kept_sites["x"],
    kept_sites["y"],
    s=80,
    color=DATA_COLOUR,
    edgecolor="white",
    linewidth=1.5,
    zorder=3,
    label="Sampling site",
)
axis.scatter(
    dropped_sites["x"],
    dropped_sites["y"],
    s=80,
    color=ABOVE_THRESHOLD_COLOUR,
    edgecolor="white",
    linewidth=1.5,
    zorder=3,
    label="Site far from its listed beach (left out)",
)

for name, x, y in beach_centres.iter_rows():
    dx, dy = LABEL_OFFSETS[name]
    axis.annotate(
        LABEL_TEXT.get(name, name),
        (x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        ha="left" if dx > 0 else "right" if dx < 0 else "center",
        va="center",
        fontsize=11,
        color=TEXT_PRIMARY,
    )
for beach, site, x, y in dropped_sites.select(
    "beachName", "siteName", "x", "y"
).iter_rows():
    offset, align = DROPPED_LABEL_PLACES[site]
    axis.annotate(
        f"{site}\n(listed as {beach})",
        (x, y),
        xytext=offset,
        textcoords="offset points",
        ha=align,
        va="bottom",
        fontsize=10,
        color=TEXT_SECONDARY,
    )

MAP_PAD = 2_500
axis.set_xlim(sites["x"].min() - MAP_PAD, sites["x"].max() + MAP_PAD)
axis.set_ylim(sites["y"].min() - MAP_PAD, sites["y"].max() + MAP_PAD)
cx.add_basemap(
    axis,
    crs="EPSG:3857",
    source=cx.providers.Esri.WorldGrayCanvas,
    attribution_size=8,
)
axis.set_axis_off()
axis.legend(loc="upper left", frameon=True, fontsize=12)
figure.tight_layout()
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
figure.savefig(FIGURE_DIR / "sampling-sites-map.png", dpi=300, bbox_inches="tight")


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

figure.tight_layout()
figure.savefig(FIGURE_DIR / "all-raw-results.png", bbox_inches="tight")


#### Summary figure: results by order of magnitude, by beach ####
# The cleaned data, so that what is drawn is exactly what the analysis uses, and
# the exclusions live in one place rather than being repeated here.
# Results are counted in bands of ten: 1 to 10, 11 to 100, and so on. Bands rather
# than narrow bars because the threshold sits on a band edge, so the share of a
# beach's results above 100 is the last two bars of its panel.
summary_results = pl.read_csv(ANALYSIS_DATA_PATH, try_parse_dates=True).with_columns(
    pl.col("eColi").log10().alias("logEColi")
)

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

figure.supylabel("Number of results", fontsize=10, color=TEXT_SECONDARY)
figure.supxlabel("E. coli per 100 mL", fontsize=10, color=TEXT_SECONDARY)
figure.tight_layout()
figure.savefig(FIGURE_DIR / "results-by-magnitude.png", bbox_inches="tight")


#### Day-level figure: every beach-day the analysis uses ####
# A beach is judged on the geometric mean of its samples for the day, so this is
# the unit the analysis works in, and the one the threshold applies to.
daily_means = (
    summary_results.group_by("beachName", "collectionDate")
    .agg(
        pl.col("logEColi").mean().alias("logGeometricMean"),
        pl.len().alias("nResults"),
    )
    # Four results, not five, so that Sunnyside's four sites are included.
    .filter(pl.col("nResults") >= MINIMUM_RESULTS)
    .with_columns(
        (pl.col("logGeometricMean") > np.log10(WARNING_THRESHOLD)).alias("overLimit")
    )
    # group_by returns rows in no fixed order. Sorting makes each day get the same
    # jitter on every run, so the seeded figure is reproducible.
    .sort("beachName", "collectionDate")
)

day_order = (
    daily_means.group_by("beachName")
    .agg(pl.col("overLimit").mean().alias("share"))
    .sort("share")["beachName"]
    .to_list()
)

figure, axis = plt.subplots(figsize=(10, 6.0))
for row, beach in enumerate(day_order):
    beach_days = daily_means.filter(pl.col("beachName") == beach)
    means = beach_days["logGeometricMean"].to_numpy()
    over = beach_days["overLimit"].to_numpy()
    height = row + rng.uniform(-0.32, 0.32, size=means.size)
    # Days over the limit carry their own hue. Position relative to the line says
    # the same thing, so colour is not doing the work alone.
    for selected, colour, opacity in (
        (~over, DATA_COLOUR, 0.22),
        (over, ABOVE_THRESHOLD_COLOUR, 0.4),
    ):
        axis.scatter(
            means[selected],
            height[selected],
            s=10,
            alpha=opacity,
            color=colour,
            linewidths=0,
            rasterized=True,
        )
    axis.text(
        1.005,
        row,
        f"{over.mean():.0%}",
        transform=axis.get_yaxis_transform(),
        va="center",
        fontsize=9,
        color=ABOVE_THRESHOLD_COLOUR,
    )

axis.axvline(
    np.log10(WARNING_THRESHOLD),
    color=TEXT_PRIMARY,
    linewidth=1,
    linestyle=(0, (6, 4)),
    zorder=3,
)
axis.xaxis.set_major_locator(FixedLocator(np.log10([10, 100, 1_000])))
axis.xaxis.set_major_formatter(count_formatter)
# Minor ticks inside each decade, so that the discrete values a geometric mean of
# five multiples of ten can take are placeable by eye.
axis.xaxis.set_minor_locator(
    FixedLocator(np.log10([20, 30, 50, 200, 300, 500, 2_000, 3_000]))
)
axis.xaxis.set_minor_formatter(count_formatter)
axis.tick_params(axis="x", which="minor", labelsize=7.5)

# The 17 days whose geometric mean falls below the reporting floor stretch the
# axis down to about 2 and squeeze everything else into the right two thirds. The
# axis starts just under the floor instead, and the caption in the paper says
# how many days that leaves out.
below_floor = daily_means.filter(
    pl.col("logGeometricMean") < np.log10(DETECTION_LIMIT)
).height
axis.set_xlim(np.log10(9), daily_means["logGeometricMean"].max() + 0.05)
axis.set_yticks(range(len(day_order)))
axis.set_yticklabels(day_order, fontsize=10, color=TEXT_PRIMARY)
axis.set_ylim(-0.7, len(day_order) - 0.3)
axis.grid(axis="x", color=GRID_COLOUR, linewidth=0.5)
axis.set_axisbelow(True)
axis.tick_params(axis="y", length=0)
axis.text(
    1.005,
    len(day_order) - 0.4,
    "Share of days\nover the limit",
    transform=axis.get_yaxis_transform(),
    va="bottom",
    fontsize=9,
    color=TEXT_SECONDARY,
)

axis.set_xlabel("E. coli per 100 mL (log scale)", fontsize=10, color=TEXT_SECONDARY)
figure.tight_layout()
figure.savefig(FIGURE_DIR / "all-beach-days.png", bbox_inches="tight")

print(f"Saved four figures to {FIGURE_DIR}")
print(f"Sampling sites mapped: {sites.height}")
print(f"Raw results plotted: {raw_results.height:,}")
print(f"Cleaned results plotted: {summary_results.height:,}")
print(f"Beach-days plotted: {daily_means.height:,}")
print(f"Beach-days with a mean below {DETECTION_LIMIT}, off the axis: {below_floor}")
