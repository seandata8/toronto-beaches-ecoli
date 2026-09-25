#### Preamble ####
# Purpose: Tests the simulated beach data written by
# `scripts/00-simulate_data.py`. The first suite checks the structure and values
# of the table itself. The second checks that the patterns built into the
# simulation are actually present, so that a change to the design that quietly
# breaks it is caught here rather than in the analysis.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars` and `pointblank` must be installed (uv add polars pointblank)
# - Run `uv run scripts/00-simulate_data.py` first
# - Run from the project root: uv run scripts/01-test_simulated_data.py


#### Workspace setup ####
import json
from datetime import date, timedelta

import pointblank as pb
import polars as pl

SIMULATED_DATA_PATH = "data/00-simulated_data/simulated_data.csv"

simulated_data = pl.read_csv(SIMULATED_DATA_PATH, try_parse_dates=True)


#### What the data should look like ####
# These expectations are written out again rather than imported from the
# simulation script, so that a mistake in the simulation cannot pass the test by
# being repeated in it.
EXPECTED_SITES_PER_BEACH = {
    "Marie Curtis Park East Beach": 5,
    "Sunnyside Beach": 4,
    "Hanlan's Point Beach": 5,
    "Gibraltar Point Beach": 5,
    "Centre Island Beach": 5,
    "Ward's Island Beach": 5,
    "Cherry Beach": 5,
    "Woodbine Beaches": 5,
    "Kew Balmy Beach": 6,
    "Bluffer's Beach Park": 5,
}
EXPECTED_BEACHES = list(EXPECTED_SITES_PER_BEACH)
EXPECTED_YEARS = list(range(2007, 2027))

DETECTION_LIMIT = 10
REPORTING_STEP = 10
WARNING_THRESHOLD = 100
MINIMUM_RESULTS = 4

# The reporting ceiling the real data acquired in 2018, and which becomes complete
# in 2026.
CEILING_VALUE = 1_000
CEILING_FIRST_YEAR = 2018
CEILING_COMPLETE_YEAR = 2026

# The two beaches given a high baseline by the simulation's seed. Changing the
# seed or the group sizes will fail the last check below, which is intended: the
# analysis is written against a known answer.
HIGH_BEACHES = ["Centre Island Beach", "Gibraltar Point Beach"]
COMMON_BEACHES = [
    beach
    for beach in EXPECTED_BEACHES
    if beach not in HIGH_BEACHES + ["Marie Curtis Park East Beach", "Woodbine Beaches"]
]


def victoria_day(year: int) -> date:
    """The Monday on or before 24 May."""
    may24 = date(year, 5, 24)
    return may24 - timedelta(days=may24.weekday())


def labour_day(year: int) -> date:
    """The first Monday in September."""
    sept1 = date(year, 9, 1)
    return sept1 + timedelta(days=-sept1.weekday() % 7)


season_days = [
    victoria_day(year) + timedelta(days=offset)
    for year in EXPECTED_YEARS
    for offset in range((labour_day(year) - victoria_day(year)).days + 1)
]
expected_rows = len(season_days) * sum(EXPECTED_SITES_PER_BEACH.values())


#### Suite 1: structure and values ####
structure = (
    pb.Validate(
        data=simulated_data,
        tbl_name="Simulated beach data",
        label="Structure and values",
    )
    # The table holds the four columns of the cleaned data, in order and typed.
    .col_schema_match(
        schema=pb.Schema(
            columns=[
                ("beachName", "String"),
                ("siteName", "String"),
                ("collectionDate", "Date"),
                ("eColi", "Int64"),
            ]
        )
    )
    .col_count_match(count=4)
    .row_count_match(count=expected_rows)
    # A row exists for every site on every sampling day, so only eColi is blank.
    .col_vals_not_null(columns=["beachName", "siteName", "collectionDate"])
    # The ten beaches of the real data, named exactly.
    .col_vals_in_set(columns="beachName", set=EXPECTED_BEACHES)
    .col_vals_regex(columns="siteName", pattern=r"^.+ site \d$")
    # Every date falls on a day of a season running Victoria Day to Labour Day.
    .col_vals_expr(expr=pl.col("collectionDate").is_in(season_days))
    # The laboratory reports in steps of ten and cannot report below ten.
    .col_vals_ge(columns="eColi", value=DETECTION_LIMIT, na_pass=True)
    .col_vals_expr(
        expr=(pl.col("eColi") % REPORTING_STEP == 0) | pl.col("eColi").is_null()
    )
    # No extreme errors: the real data's single implausible reading is removed in
    # cleaning, so the simulation matches cleaned data.
    .col_vals_lt(columns="eColi", value=100_000, na_pass=True)
    # One sample per site per day.
    .rows_distinct(columns_subset=["siteName", "collectionDate"])
    .interrogate()
)


#### Derived tables ####
results = simulated_data.drop_nulls("eColi")

beach_days = simulated_data.group_by("beachName", "collectionDate").agg(
    pl.col("eColi").is_not_null().sum().alias("nResults"),
    pl.len().alias("nSites"),
)

# The daily geometric mean, computed only when at least four results are
# available, and whether it exceeded the threshold.
daily_means = (
    results.with_columns(pl.col("eColi").log10().alias("logEColi"))
    .group_by("beachName", "collectionDate")
    .agg(
        pl.col("logEColi").mean().alias("logGeometricMean"),
        pl.len().alias("nResults"),
    )
    .filter(pl.col("nResults") >= MINIMUM_RESULTS)
    .with_columns(
        (pl.col("logGeometricMean") > pl.lit(WARNING_THRESHOLD).log10()).alias(
            "exceeds"
        )
    )
    .sort("beachName", "collectionDate")
)

# Pairs of consecutive days at the same beach, as the analysis will use them.
consecutive_days = daily_means.with_columns(
    pl.col("logGeometricMean").shift(1).over("beachName").alias("previousMean"),
    pl.col("collectionDate").shift(1).over("beachName").alias("previousDate"),
).filter((pl.col("collectionDate") - pl.col("previousDate")).dt.total_days() == 1)

# Exceedance days per beach per year, for the comparison with Poisson.
per_year = (
    daily_means.with_columns(pl.col("collectionDate").dt.year().alias("year"))
    .group_by("beachName", "year")
    .agg(pl.col("exceeds").sum().alias("exceedanceDays"))
)

exceedance_by_beach = daily_means.group_by("beachName").agg(
    pl.col("exceeds").mean().alias("exceedanceShare")
)


def mean_exceedance(beaches: list[str]) -> float:
    """Average exceedance share across the named beaches."""
    return exceedance_by_beach.filter(pl.col("beachName").is_in(beaches))[
        "exceedanceShare"
    ].mean()


#### Suite 2: the patterns built into the simulation ####
# Each row is one thing the design promises, with the bounds set loosely on
# purpose: these are properties of random data, so a tight bound would fail on
# some seeds while telling us nothing about the design.
sites_per_beach = (
    simulated_data.group_by("beachName")
    .agg(
        pl.col("siteName").n_unique().alias("nSites"),
        pl.col("collectionDate").dt.year().n_unique().alias("nYears"),
    )
    .with_columns(
        pl.col("beachName")
        .replace_strict(EXPECTED_SITES_PER_BEACH, return_dtype=pl.Int64)
        .alias("expectedSites")
    )
)

blank_rows = simulated_data.height - results.height
blanks_in_empty_beach_days = beach_days.filter(pl.col("nResults") == 0)["nSites"].sum()

# The ceiling applies only from 2018, and completely from 2026, so the record is
# split to check that each period behaves as designed.
sample_year = pl.col("collectionDate").dt.year()
before_ceiling = results.filter(sample_year < CEILING_FIRST_YEAR)
after_ceiling = results.filter(
    (sample_year >= CEILING_FIRST_YEAR) & (sample_year < CEILING_COMPLETE_YEAR)
)
fully_capped = results.filter(sample_year >= CEILING_COMPLETE_YEAR)

design = pl.DataFrame(
    {
        "check": [
            "share of results at the detection limit",
            "share of samples blank",
            "share of blanks that are whole beach-days",
            "share of beach-days with at least four results",
            "correlation between consecutive days",
            "variance of exceedance days over its mean",
            "exceedance share of high beaches over common ones",
            "share above the ceiling before 2018",
            "share at the ceiling from 2018 to 2025",
            "share above the ceiling from 2018 to 2025",
            "share above the ceiling from 2026",
        ],
        "value": [
            (results["eColi"] == DETECTION_LIMIT).mean(),
            blank_rows / simulated_data.height,
            blanks_in_empty_beach_days / blank_rows,
            (beach_days["nResults"] >= MINIMUM_RESULTS).mean(),
            consecutive_days.select(pl.corr("logGeometricMean", "previousMean")).item(),
            per_year["exceedanceDays"].var() / per_year["exceedanceDays"].mean(),
            mean_exceedance(HIGH_BEACHES) - mean_exceedance(COMMON_BEACHES),
            # Before 2018 nothing is capped, so high readings must survive.
            (before_ceiling["eColi"] > CEILING_VALUE).mean(),
            (after_ceiling["eColi"] == CEILING_VALUE).mean(),
            # The 2018 ceiling is partial: some high readings still get through.
            (after_ceiling["eColi"] > CEILING_VALUE).mean(),
            # From 2026 it is complete, so nothing at all may exceed it.
            (fully_capped["eColi"] > CEILING_VALUE).mean(),
        ],
        # Bounds are read from the real data where one exists, and from the
        # design otherwise.
        "lower": [0.40, 0.02, 0.85, 0.90, 0.20, 1.50, 0.05, 0.005, 0.004, 0.0005, 0.0],
        "upper": [0.55, 0.05, 1.00, 1.00, 0.70, 20.0, 0.40, 0.020, 0.020, 0.0100, 0.0],
    }
)

built_in = (
    pb.Validate(
        data=design,
        tbl_name="Simulated beach data",
        label="Patterns built into the simulation",
    )
    .col_vals_between(columns="value", left=pb.col("lower"), right=pb.col("upper"))
    .interrogate()
)

# Site counts and year coverage, checked beach by beach.
coverage = (
    pb.Validate(
        data=sites_per_beach,
        tbl_name="Simulated beach data",
        label="Sites and years per beach",
    )
    .col_vals_expr(expr=pl.col("nSites") == pl.col("expectedSites"))
    .col_vals_eq(columns="nYears", value=len(EXPECTED_YEARS))
    .interrogate()
)


#### Report ####
def print_report(validation: pb.Validate) -> None:
    """Print one row per check: what was checked, and how many values passed.

    The report is built from pointblank's JSON rather than its own dataframe
    report, because that report cannot be built when a step checks several
    columns at once, as `rows_distinct()` does here.
    """
    steps = [
        {
            "step": step["i"],
            "check": step["assertion_type"],
            "column": str(step["column"]),
            "values": step["n"],
            "passed": step["n_passed"],
            "failed": step["n_failed"],
        }
        for step in json.loads(validation.get_json_report())
    ]
    with pl.Config(tbl_rows=-1, fmt_str_lengths=40, tbl_hide_dataframe_shape=True):
        print(pl.DataFrame(steps))


for validation in (structure, built_in, coverage):
    print(f"\n{validation.label}")
    print_report(validation)

print("\nMeasured values behind the second suite:")
with pl.Config(tbl_rows=-1, fmt_str_lengths=60, tbl_hide_dataframe_shape=True):
    print(design.select("check", pl.col("value").round(3), "lower", "upper"))

for validation in (structure, built_in, coverage):
    validation.assert_passing()

print("\nAll checks passed.")
