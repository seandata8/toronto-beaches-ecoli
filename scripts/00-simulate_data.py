#### Preamble ####
# Purpose: Simulates E. coli results for Toronto's supervised beaches, with the
# same structure as the cleaned City of Toronto data and with differences
# between beaches built in on purpose, so the planned analysis can be tested on
# data whose answer is known. The design is described in
# `other/notes/analysis_plan.md`.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars` and `numpy` must be installed (uv add polars numpy)
# - Run from the project root: uv run scripts/00-simulate_data.py


#### Workspace setup ####
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

SEED = 853
OUTPUT_PATH = Path("data/00-simulated_data/simulated_data.csv")

rng = np.random.default_rng(SEED)


#### Settings ####
# Seasons run from Victoria Day to Labour Day, as in the real data.
FIRST_YEAR = 2007
LAST_YEAR = 2026

# Sites per beach, matching the real data before 2026.
SITES_PER_BEACH = {
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

# E. coli is built on a log10 scale by adding four parts: a beach baseline, a
# city-wide daily effect, a beach daily effect and site noise. Each spread below
# is the standard deviation of that part on its own, once the carry-over has
# settled down, so the four add up as squares.
COMMON_BASELINE = 1.10
MODERATE_LIFT = 0.20
HIGH_LIFT = 0.40

CITY_CARRY_OVER = 0.5
CITY_SD = 0.30

BEACH_CARRY_OVER = 0.5
BEACH_SD = 0.34

SITE_SD = 0.50

# Sunnyside (4 sites) and Kew Balmy (6 sites) are held at the common baseline on
# purpose, so their results measure the effect of the site count on its own.
COMMON_BY_DESIGN = ["Sunnyside Beach", "Kew Balmy Beach"]
N_MODERATE = 2
N_HIGH = 2

# The laboratory reports in steps of 10 and cannot report below 10.
REPORTING_STEP = 10
DETECTION_LIMIT = 10

# A row is kept for every site on every sampling day even when no test was done.
# In the real data 95% of blanks are whole beach-days rather than single samples:
# 672 of 20,462 beach-days have no results at all, and only 128 are partly blank.
BLANK_BEACH_DAY_SHARE = 0.032
BLANK_SAMPLE_SHARE = 0.002
N_BLANK_DAYS = 3


#### Season calendar ####
def victoria_day(year: int) -> date:
    """The Monday on or before 24 May."""
    may24 = date(year, 5, 24)
    return may24 - timedelta(days=may24.weekday())


def labour_day(year: int) -> date:
    """The first Monday in September."""
    sept1 = date(year, 9, 1)
    return sept1 + timedelta(days=-sept1.weekday() % 7)


def season_dates(year: int) -> list[date]:
    """Every day from Victoria Day to Labour Day inclusive."""
    start, end = victoria_day(year), labour_day(year)
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


#### Beach baselines ####
beaches = list(SITES_PER_BEACH)

# The groups are made up. They are not based on the real data.
assignable = [beach for beach in beaches if beach not in COMMON_BY_DESIGN]
lifted = rng.choice(assignable, size=N_MODERATE + N_HIGH, replace=False)
moderate_beaches = set(lifted[:N_MODERATE])
high_beaches = set(lifted[N_MODERATE:])

baselines = {}
for beach in beaches:
    lift = 0.0
    if beach in moderate_beaches:
        lift = MODERATE_LIFT
    elif beach in high_beaches:
        lift = HIGH_LIFT
    baselines[beach] = COMMON_BASELINE + lift


#### Daily effects ####
def carried_over_series(n_days: int, carry_over: float, spread: float) -> np.ndarray:
    """A series where each day keeps a fraction of the day before, plus new noise.

    `spread` is the standard deviation of the settled series, so raising the
    carry-over changes how persistent the series is without widening it.
    """
    innovation_sd = spread * np.sqrt(1 - carry_over**2)
    series = np.empty(n_days)
    series[0] = rng.normal(0, spread)
    for day in range(1, n_days):
        series[day] = carry_over * series[day - 1] + rng.normal(0, innovation_sd)
    return series


#### Simulate data ####
# Each season starts fresh: the carry-over runs within a season, not across the
# winter between them.
rows = []
for year in range(FIRST_YEAR, LAST_YEAR + 1):
    dates = season_dates(year)
    n_days = len(dates)

    city_effect = carried_over_series(n_days, CITY_CARRY_OVER, CITY_SD)

    for beach in beaches:
        beach_effect = carried_over_series(n_days, BEACH_CARRY_OVER, BEACH_SD)
        n_sites = SITES_PER_BEACH[beach]
        site_names = [f"{beach} site {site + 1}" for site in range(n_sites)]

        site_noise = rng.normal(0, SITE_SD, size=(n_days, n_sites))
        log_results = (
            baselines[beach] + city_effect[:, None] + beach_effect[:, None] + site_noise
        )

        for day, sampling_date in enumerate(dates):
            for site, site_name in enumerate(site_names):
                rows.append((beach, site_name, sampling_date, log_results[day, site]))

simulated_data = pl.DataFrame(
    rows,
    schema={
        "beachName": pl.String,
        "siteName": pl.String,
        "collectionDate": pl.Date,
        "logEColi": pl.Float64,
    },
    orient="row",
)


#### Report as the laboratory would ####
# Results are rounded to the nearest 10, and anything below the detection limit
# is reported as 10.
simulated_data = simulated_data.with_columns(
    pl.max_horizontal(
        (10 ** pl.col("logEColi") / REPORTING_STEP).round() * REPORTING_STEP,
        pl.lit(DETECTION_LIMIT),
    )
    .cast(pl.Int64)
    .alias("eColi")
).drop("logEColi")


#### Add missing results ####
# Missing results come in three ways: a whole beach-day untested, which is by far
# the most common; the occasional single sample; and a few days when no beach was
# tested at all.
beach_days = (
    simulated_data.select("beachName", "collectionDate")
    .unique()
    .sort("beachName", "collectionDate")
)
blank_beach_days = beach_days.filter(
    rng.random(beach_days.height) < BLANK_BEACH_DAY_SHARE
).with_columns(pl.lit(True).alias("blankBeachDay"))

all_dates = simulated_data["collectionDate"].unique().sort()
blank_dates = rng.choice(all_dates.to_numpy(), size=N_BLANK_DAYS, replace=False)
blank_sample = rng.random(simulated_data.height) < BLANK_SAMPLE_SHARE

simulated_data = (
    simulated_data.join(
        blank_beach_days, on=["beachName", "collectionDate"], how="left"
    )
    .with_columns(
        pl.when(
            pl.col("blankBeachDay").fill_null(False)
            | pl.Series(blank_sample)
            | pl.col("collectionDate").is_in(blank_dates.tolist())
        )
        .then(None)
        .otherwise(pl.col("eColi"))
        .alias("eColi")
    )
    .drop("blankBeachDay")
)


#### Save data ####
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
simulated_data.write_csv(OUTPUT_PATH)
print(f"Saved {simulated_data.height} rows to {OUTPUT_PATH}")


#### Summarise what was built in ####
print("\nBeach baselines (log10 scale):")
for beach in beaches:
    group = (
        "high"
        if beach in high_beaches
        else "moderate"
        if beach in moderate_beaches
        else "common"
    )
    print(f"  {beach:<30} {baselines[beach]:.2f}  {group}")

results = simulated_data.drop_nulls("eColi")
print(f"\nResults: {results.height}")
print(f"At the detection limit: {(results['eColi'] == DETECTION_LIMIT).mean():.1%}")
print(f"Blank: {simulated_data['eColi'].is_null().mean():.1%}")
