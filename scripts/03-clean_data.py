#### Preamble ####
# Purpose: Cleans the Toronto beach water quality data downloaded by
# `scripts/02-download_data.py` into the dataset the paper analyses. Every
# decision here is set out in `other/notes/analysis_plan.md`; the reasons behind
# them are in `other/notes/raw_data_findings.md`.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars` must be installed (uv add polars)
# - Run `uv run scripts/02-download_data.py` first
# - Run from the project root: uv run scripts/03-clean_data.py


#### Workspace setup ####
from datetime import date, timedelta
from pathlib import Path

import polars as pl

RAW_DATA_PATH = "data/01-raw_data/raw_data.csv"
OUTPUT_PATH = Path("data/02-analysis_data/analysis_data.csv")

# Results above this are treated as errors. Only one reading in the record
# qualifies: 6,191,768 at Marie Curtis Park East Beach on 15 June 2009, which is
# about 390 times the next highest reading ever recorded.
IMPLAUSIBLE_RESULT = 100_000

# Two sites added in 2026 and listed under beaches 14 to 16 km away. Every other
# site sits within 0.4 km of the rest of its beach. On 25 September 2026 the City
# said the listing had been referred for correction, without naming the right
# beach, so they are left out. A later download may list them differently.
MISLABELLED_SITES = ["60W", "GP6"]


#### Season calendar ####
# The City describes the season as June to Labour Day, but sampling has begun the
# day after Victoria Day in most years since 2012. The window keeps those days.
def victoria_day(year: int) -> date:
    """The Monday on or before 24 May."""
    may24 = date(year, 5, 24)
    return may24 - timedelta(days=may24.weekday())


def labour_day(year: int) -> date:
    """The first Monday in September."""
    sept1 = date(year, 9, 1)
    return sept1 + timedelta(days=-sept1.weekday() % 7)


#### Clean data ####
raw_data = pl.read_csv(RAW_DATA_PATH, infer_schema_length=None)

analysis_data = (
    raw_data.with_columns(
        pl.col("collectionDate").str.to_date().alias("collectionDate"),
        # `geometry` holds GeoJSON with longitude first, then latitude. Splitting
        # it into two columns means no later step has to remember that order.
        pl.col("geometry")
        .str.extract(r"\[\[(-?\d+\.\d+)", 1)
        .cast(pl.Float64)
        .alias("longitude"),
        pl.col("geometry")
        .str.extract(r",\s*(-?\d+\.\d+)\]\]", 1)
        .cast(pl.Float64)
        .alias("latitude"),
    )
    # A row with no result is a day when no test was done, not a measurement.
    .drop_nulls("eColi")
    .filter(pl.col("eColi") < IMPLAUSIBLE_RESULT)
    .filter(~pl.col("siteName").is_in(MISLABELLED_SITES))
    .with_columns(pl.col("collectionDate").dt.year().alias("year"))
    # Keep the season, which also removes the stray dates outside it, such as
    # 2 March 2017, and the placeholder rows after Labour Day.
    .filter(
        pl.col("collectionDate").is_between(
            pl.col("year").map_elements(victoria_day, return_dtype=pl.Date),
            pl.col("year").map_elements(labour_day, return_dtype=pl.Date),
        )
    )
    .select(
        "beachId",
        "beachName",
        "siteName",
        "collectionDate",
        "year",
        "eColi",
        "longitude",
        "latitude",
    )
    .sort("beachName", "collectionDate", "siteName")
)


#### Save data ####
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
analysis_data.write_csv(OUTPUT_PATH)


#### Report what was removed ####
print(f"Saved {analysis_data.height:,} rows to {OUTPUT_PATH}")
print(f"Raw rows: {raw_data.height:,}")

removed = {
    "no result recorded": raw_data.filter(pl.col("eColi").is_null()).height,
    "implausible result": raw_data.filter(pl.col("eColi") >= IMPLAUSIBLE_RESULT).height,
    "mislabelled site": raw_data.filter(
        pl.col("siteName").is_in(MISLABELLED_SITES) & pl.col("eColi").is_not_null()
    ).height,
}
for reason, rows in removed.items():
    print(f"  {reason:<20} {rows:>7,}")
print(
    f"  {'outside the season':<20} {raw_data.height - analysis_data.height - sum(removed.values()):>7,}"
)

print(f"\nYears: {analysis_data['year'].min()} to {analysis_data['year'].max()}")
print(f"Beaches: {analysis_data['beachName'].n_unique()}")
print(f"Sites: {analysis_data['siteName'].n_unique()}")
