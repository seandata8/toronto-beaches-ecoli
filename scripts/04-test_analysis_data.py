#### Preamble ####
# Purpose: Tests the cleaned beach data written by `scripts/03-clean_data.py`.
# The first suite checks the structure and values of the table, the second that
# cleaning did what it claims, and the third records the properties of the data
# the analysis has to work around: the reporting floor, the ceiling that arrived
# in 2018, and the number of sites per beach.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars` and `pointblank` must be installed (uv add polars pointblank)
# - Run `uv run scripts/03-clean_data.py` first
# - Run from the project root: uv run scripts/04-test_analysis_data.py


#### Workspace setup ####
import json
from datetime import date, timedelta

import pointblank as pb
import polars as pl

ANALYSIS_DATA_PATH = "data/02-analysis_data/analysis_data.csv"

analysis_data = pl.read_csv(ANALYSIS_DATA_PATH, try_parse_dates=True)


#### What the data should look like ####
# Written out again rather than imported from the cleaning script, so that a
# mistake there cannot pass the test by being repeated here.
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
MINIMUM_RESULTS = 4
IMPLAUSIBLE_RESULT = 100_000
REMOVED_SITES = ["60W", "GP6"]

# The ceiling the laboratory's reporting acquired in 2018, complete in 2026.
CEILING_VALUE = 1_000
CEILING_FIRST_YEAR = 2018
CEILING_COMPLETE_YEAR = 2026

# Toronto's supervised beaches, generously bounded.
LONGITUDE_RANGE = (-79.6, -79.2)
LATITUDE_RANGE = (43.5, 43.8)


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


#### Suite 1: structure and values ####
structure = (
    pb.Validate(
        data=analysis_data,
        tbl_name="Cleaned beach data",
        label="Structure and values",
    )
    .col_schema_match(
        schema=pb.Schema(
            columns=[
                ("beachId", "Int64"),
                ("beachName", "String"),
                ("siteName", "String"),
                ("collectionDate", "Date"),
                ("year", "Int64"),
                ("eColi", "Int64"),
                ("longitude", "Float64"),
                ("latitude", "Float64"),
            ]
        )
    )
    # Cleaning drops every row without a result, so nothing anywhere is missing.
    .col_vals_not_null(columns=analysis_data.columns)
    .col_vals_in_set(columns="beachName", set=EXPECTED_BEACHES)
    .col_vals_not_in_set(columns="siteName", set=REMOVED_SITES)
    .col_vals_in_set(columns="year", set=EXPECTED_YEARS)
    # Every date falls within its own season, Victoria Day to Labour Day.
    .col_vals_expr(expr=pl.col("collectionDate").is_in(season_days))
    .col_vals_expr(expr=pl.col("collectionDate").dt.year() == pl.col("year"))
    # Results are positive and below the level treated as an error. Unlike the
    # simulated data, the real data is not all at or above 10 and not all in
    # steps of 10: 63 readings are lower and 132 are not multiples. Those are
    # published values, so cleaning leaves them alone and the share is checked
    # in the third suite instead.
    .col_vals_gt(columns="eColi", value=0)
    .col_vals_lt(columns="eColi", value=IMPLAUSIBLE_RESULT)
    .col_vals_between(
        columns="longitude", left=LONGITUDE_RANGE[0], right=LONGITUDE_RANGE[1]
    )
    .col_vals_between(
        columns="latitude", left=LATITUDE_RANGE[0], right=LATITUDE_RANGE[1]
    )
    # One result per site per day.
    .rows_distinct(columns_subset=["siteName", "collectionDate"])
    .interrogate()
)


#### Suite 2: each beach and site ####
per_beach = (
    analysis_data.group_by("beachName")
    .agg(
        pl.col("siteName").n_unique().alias("nSites"),
        pl.col("beachId").n_unique().alias("nIds"),
        pl.col("year").n_unique().alias("nYears"),
    )
    .with_columns(
        pl.col("beachName")
        .replace_strict(EXPECTED_SITES_PER_BEACH, return_dtype=pl.Int64)
        .alias("expectedSites")
    )
)

# Each site is one fixed place: a site whose coordinates move would mean the
# geometry was parsed wrongly, or that a site was renamed.
per_site = analysis_data.group_by("siteName").agg(
    pl.col("longitude").n_unique().alias("nLongitudes"),
    pl.col("latitude").n_unique().alias("nLatitudes"),
    pl.col("beachName").n_unique().alias("nBeaches"),
)

coverage = (
    pb.Validate(
        data=per_beach,
        tbl_name="Cleaned beach data",
        label="Sites and years per beach",
    )
    .col_vals_expr(expr=pl.col("nSites") == pl.col("expectedSites"))
    .col_vals_eq(columns="nIds", value=1)
    .col_vals_eq(columns="nYears", value=len(EXPECTED_YEARS))
    .interrogate()
)

sites = (
    pb.Validate(
        data=per_site,
        tbl_name="Cleaned beach data",
        label="One fixed place per site",
    )
    .col_vals_eq(columns="nLongitudes", value=1)
    .col_vals_eq(columns="nLatitudes", value=1)
    .col_vals_eq(columns="nBeaches", value=1)
    .interrogate()
)


#### Suite 3: what the analysis has to work around ####
# These are properties of the City's data rather than mistakes. They are checked
# so that a change in the City's reporting shows up here, where it can be thought
# about, rather than quietly altering a result.
year = pl.col("year")
before_ceiling = analysis_data.filter(year < CEILING_FIRST_YEAR)
after_ceiling = analysis_data.filter(
    (year >= CEILING_FIRST_YEAR) & (year < CEILING_COMPLETE_YEAR)
)
fully_capped = analysis_data.filter(year >= CEILING_COMPLETE_YEAR)

beach_days = analysis_data.group_by("beachName", "collectionDate").agg(
    pl.len().alias("nResults")
)

reporting = pl.DataFrame(
    {
        "check": [
            "share of results at the reporting floor",
            "share of results below the floor",
            "share of results in multiples of ten",
            "share of beach-days with at least four results",
            "share above the ceiling before 2018",
            "share at the ceiling from 2018 to 2025",
            "share above the ceiling from 2018 to 2025",
            "share above the ceiling from 2026",
        ],
        "value": [
            (analysis_data["eColi"] == DETECTION_LIMIT).mean(),
            (analysis_data["eColi"] < DETECTION_LIMIT).mean(),
            (analysis_data["eColi"] % REPORTING_STEP == 0).mean(),
            (beach_days["nResults"] >= MINIMUM_RESULTS).mean(),
            (before_ceiling["eColi"] > CEILING_VALUE).mean(),
            (after_ceiling["eColi"] == CEILING_VALUE).mean(),
            (after_ceiling["eColi"] > CEILING_VALUE).mean(),
            (fully_capped["eColi"] > CEILING_VALUE).mean(),
        ],
        # Bounds are wide enough to survive another year of data, and tight
        # enough to catch a change in how the City reports.
        "lower": [0.40, 0.0, 0.99, 0.95, 0.005, 0.005, 0.0005, 0.0],
        "upper": [0.55, 0.005, 1.00, 1.00, 0.030, 0.030, 0.0200, 0.0],
    }
)

reporting_checks = (
    pb.Validate(
        data=reporting,
        tbl_name="Cleaned beach data",
        label="Reporting floor, ceiling and coverage",
    )
    .col_vals_between(columns="value", left=pb.col("lower"), right=pb.col("upper"))
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


validations = (structure, coverage, sites, reporting_checks)
for validation in validations:
    print(f"\n{validation.label}")
    print_report(validation)

print("\nMeasured values behind the third suite:")
with pl.Config(tbl_rows=-1, fmt_str_lengths=60, tbl_hide_dataframe_shape=True):
    print(reporting.select("check", pl.col("value").round(4), "lower", "upper"))

for validation in validations:
    validation.assert_passing()

print("\nAll checks passed.")
