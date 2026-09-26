#### Preamble ####
# Purpose: Draws the three figures that show the whole dataset: a map of the
# sampling sites; every published result over time, including the one that
# cleaning removes; and a histogram of every beach-day, the unit the analysis
# uses, for each beach. The figures are saved to `paper/figures/`
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
axis.set_ylabel(
    r"$\it{E.\,coli}$ per 100 mL (log scale)", fontsize=10, color=TEXT_SECONDARY
)

figure.tight_layout()
figure.savefig(FIGURE_DIR / "all-raw-results.png", bbox_inches="tight")


#### Beach-day histogram: how often each beach goes over the limit ####
# The cleaned data, so that what is drawn is exactly what the analysis uses.
summary_results = pl.read_csv(ANALYSIS_DATA_PATH, try_parse_dates=True).with_columns(
    pl.col("eColi").log10().alias("logEColi")
)

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
)

# Half-log bins. Bins include their upper edge, so a day at exactly 100 falls in
# 30-100 and is not over the limit. The lowest bin also holds the 17 days whose
# mean is below the reporting floor of 10.
BIN_EDGES = np.log10([30, 100, 300, 1_000, 3_000])
BIN_LABELS = ["≤30", "30–100", "100–300", "300–1,000", "1,000–3,000", "3,000–10,000"]
FIRST_BIN_OVER_LIMIT = 2

binned_days = daily_means.with_columns(
    pl.col("logGeometricMean")
    .cut(BIN_EDGES.tolist(), labels=[str(i) for i in range(len(BIN_LABELS))])
    .cast(pl.Int8)
    .alias("bin")
)
day_shares = (
    daily_means.group_by("beachName")
    .agg(pl.col("overLimit").mean().alias("share"))
    .sort("share", descending=True)
)

figure, axes = plt.subplots(2, 5, figsize=(10, 6.6), sharex=True, sharey=True)
for axis, (beach, share) in zip(axes.flat, day_shares.iter_rows()):
    beach_days = binned_days.filter(pl.col("beachName") == beach)
    heights = [
        beach_days.filter(pl.col("bin") == i).height for i in range(len(BIN_LABELS))
    ]
    # Bins over the limit take their own hue, so a panel can be read without
    # tracing back to the dashed line.
    colours = [
        ABOVE_THRESHOLD_COLOUR if i >= FIRST_BIN_OVER_LIMIT else DATA_COLOUR
        for i in range(len(BIN_LABELS))
    ]
    axis.bar(range(len(BIN_LABELS)), heights, color=colours, width=0.8)
    # The limit falls on the edge between the second and third bins.
    axis.vlines(
        FIRST_BIN_OVER_LIMIT - 0.5,
        0,
        1_500,
        color=TEXT_PRIMARY,
        linewidth=1,
        linestyle=(0, (6, 4)),
    )
    axis.set_title(fill(beach, width=18), fontsize=9.5, loc="left")
    axis.text(
        0.97,
        0.80,
        f"{share:.0%} of days\nover the limit",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        fontweight="bold",
        color=ABOVE_THRESHOLD_COLOUR,
    )
    axis.set_xticks(range(len(BIN_LABELS)))
    axis.set_xticklabels(BIN_LABELS, fontsize=7, rotation=90)
    axis.grid(axis="y", color=GRID_COLOUR, linewidth=0.5)
    axis.set_axisbelow(True)

figure.supylabel("Number of beach-days", fontsize=10, color=TEXT_SECONDARY)
figure.supxlabel(
    r"Daily geometric mean, $\it{E.\,coli}$ per 100 mL",
    fontsize=10,
    color=TEXT_SECONDARY,
)
figure.tight_layout()
figure.savefig(FIGURE_DIR / "beach-day-histogram.png", bbox_inches="tight")

below_floor = daily_means.filter(
    pl.col("logGeometricMean") < np.log10(DETECTION_LIMIT)
).height

print(f"Saved three figures to {FIGURE_DIR}")
print(f"Sampling sites mapped: {sites.height}")
print(f"Raw results plotted: {raw_results.height:,}")
print(f"Beach-days plotted: {daily_means.height:,}")
print(
    f"Beach-days with a mean below {DETECTION_LIMIT}, in the lowest bin: {below_floor}"
)
