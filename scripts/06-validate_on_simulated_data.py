#### Preamble ####
# Purpose: Runs the paper's analysis on the simulated data, where the answer is
# known, and checks that it recovers what was built in. The simulation gives two
# beaches a baseline 0.4 higher on the log10 scale, two 0.2 higher, and holds the
# other six level, so the analysis should find that pattern and no more. This is
# run before the same analysis touches the real data.
# Author: Sean Murphy
# Date: 23 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars`, `numpy` and `statsmodels` must be installed
# - Run `uv run scripts/00-simulate_data.py` first
# - Run from the project root: uv run scripts/06-validate_on_simulated_data.py


#### Workspace setup ####
import polars as pl

from toronto_beaches_ecoli.analysis import (
    consecutive_day_pairs,
    daily_geometric_means,
    day_to_day_correlation,
    exceedance_by_beach,
    fit_beach_model,
    pairwise_differences,
    standard_error_inflation,
    warning_agreement,
)

SIMULATED_DATA_PATH = "data/00-simulated_data/simulated_data.csv"
# The same draws without the laboratory's floor, rounding and ceiling. Comparing
# the two says how much the censoring shrinks the gaps between beaches.
UNCENSORED_DATA_PATH = "data/00-simulated_data/simulated_data_uncensored.csv"
# The gaps table the paper prints in its appendix.
GAPS_PATH = "other/results/simulation-gaps.csv"

# What the simulation built in, repeated here rather than imported, so that a
# change to the simulation has to be noticed rather than followed silently.
HIGH_BEACHES = ["Centre Island Beach", "Gibraltar Point Beach"]
MODERATE_BEACHES = ["Marie Curtis Park East Beach", "Woodbine Beaches"]
HIGH_LIFT = 0.40
MODERATE_LIFT = 0.20
CARRY_OVER = 0.5

simulated_data = pl.read_csv(SIMULATED_DATA_PATH, try_parse_dates=True).drop_nulls(
    "eColi"
)
uncensored_data = pl.read_csv(UNCENSORED_DATA_PATH, try_parse_dates=True).drop_nulls(
    "eColi"
)
daily = daily_geometric_means(simulated_data)
uncensored_daily = daily_geometric_means(uncensored_data)


def group_gaps(fitted) -> tuple[float, float]:
    """How far the high and moderate beaches sit above the six built level.

    Each coefficient is a beach's gap from the day's average, so the built-in
    lifts appear as differences between the groups rather than as the lifts
    themselves.
    """
    estimates = dict(
        zip(
            [
                name.removeprefix("beach[").removesuffix("]")
                for name in fitted.params.index
            ],
            fitted.params.to_numpy(),
        )
    )
    high = [plain(beach) for beach in HIGH_BEACHES]
    moderate = [plain(beach) for beach in MODERATE_BEACHES]
    common = [name for name in estimates if name not in high + moderate]
    level = sum(estimates[name] for name in common) / len(common)
    return (
        sum(estimates[name] for name in high) / len(high) - level,
        sum(estimates[name] for name in moderate) / len(moderate) - level,
    )


def plain(beach: str) -> str:
    """The beach name as the model formula spells it."""
    return "".join(character for character in beach if character.isalpha())


#### Collect what the analysis finds ####
shares = exceedance_by_beach(daily)
model = fit_beach_model(daily)
differences = pairwise_differences(model)
pairs = consecutive_day_pairs(daily)
correlation = day_to_day_correlation(pairs)
agreement = warning_agreement(pairs)

coefficients = pl.DataFrame(
    {
        "beach": [
            name.removeprefix("beach[").removesuffix("]") for name in model.params.index
        ],
        "estimate": model.params.to_numpy(),
    }
).with_columns(
    pl.when(pl.col("beach").is_in([plain(beach) for beach in HIGH_BEACHES]))
    .then(pl.lit("high"))
    .when(pl.col("beach").is_in([plain(beach) for beach in MODERATE_BEACHES]))
    .then(pl.lit("moderate"))
    .otherwise(pl.lit("common"))
    .alias("group")
)

high_gap, moderate_gap = group_gaps(model)
uncensored_high_gap, uncensored_moderate_gap = group_gaps(
    fit_beach_model(uncensored_daily)
)
# How much of the built-in gap survives the laboratory's floor and ceiling.
attenuation = high_gap / uncensored_high_gap

# Pairs of beaches the simulation built at the same level. Any difference the
# analysis declares between two of these is a false positive.
common_names = coefficients.filter(pl.col("group") == "common")["beach"].to_list()
common_pairs = differences.filter(
    pl.col("beachA").is_in(common_names) & pl.col("beachB").is_in(common_names)
)
false_positives = common_pairs.filter(pl.col("differs")).height

# Every pair that crosses from a high beach to a common one should be found.
high_names = coefficients.filter(pl.col("group") == "high")["beach"].to_list()
crossing_pairs = differences.filter(
    (pl.col("beachA").is_in(high_names) & pl.col("beachB").is_in(common_names))
    | (pl.col("beachB").is_in(high_names) & pl.col("beachA").is_in(common_names))
)
found = crossing_pairs.filter(pl.col("differs")).height


#### Check it against what was built in ####
checks = [
    (
        "the two high beaches have the largest shares over the limit",
        set(shares.head(2)["beachName"].to_list()) == set(HIGH_BEACHES),
        f"top two: {', '.join(shares.head(2)['beachName'].to_list())}",
    ),
    (
        "the model recovers the 0.40 lift of the high beaches, uncensored",
        abs(uncensored_high_gap - HIGH_LIFT) < 0.05,
        f"estimated {uncensored_high_gap:.3f}, built in {HIGH_LIFT}",
    ),
    (
        "the model recovers the 0.20 lift of the moderate beaches, uncensored",
        abs(uncensored_moderate_gap - MODERATE_LIFT) < 0.06,
        f"estimated {uncensored_moderate_gap:.3f}, built in {MODERATE_LIFT}",
    ),
    (
        "the floor and ceiling shrink the gaps rather than reversing them",
        0.4 < attenuation < 0.9,
        f"{attenuation:.0%} of the gap survives the censoring",
    ),
    (
        "the censored estimates still rank the groups correctly",
        high_gap > moderate_gap > 0,
        f"high {high_gap:.3f}, moderate {moderate_gap:.3f}",
    ),
    (
        "every high-to-common pair is found",
        found == crossing_pairs.height,
        f"{found} of {crossing_pairs.height}",
    ),
    (
        "few false differences among the beaches built level",
        false_positives <= 2,
        f"{false_positives} of {common_pairs.height} pairs",
    ),
    (
        "grouping days by month widens the standard errors, as the carry-over implies",
        standard_error_inflation(daily)["ratio"].median() > 1.2,
        f"median ratio {standard_error_inflation(daily)['ratio'].median():.2f}",
    ),
    (
        "one day predicts the next, as the carry-over implies",
        0.2 < correlation["all pairs"] < CARRY_OVER + 0.25,
        f"correlation {correlation['all pairs']:.3f}, carry-over {CARRY_OVER}",
    ),
    (
        "dropping pairs with both days at the floor lowers the correlation",
        correlation["excluding pairs with both days at the floor"]
        < correlation["all pairs"],
        (
            f"{correlation['excluding pairs with both days at the floor']:.3f}"
            f" against {correlation['all pairs']:.3f}"
        ),
    ),
]


#### Report ####
print("Shares of days over the limit, as the analysis finds them:")
with pl.Config(tbl_rows=-1, tbl_hide_dataframe_shape=True):
    print(shares.with_columns(pl.col("share").round(3)))

print("\nBeach coefficients, grouped by what was built in:")
with pl.Config(tbl_rows=-1, tbl_hide_dataframe_shape=True):
    print(coefficients.with_columns(pl.col("estimate").round(3)).sort("estimate"))

print("\nGaps over the six beaches built level, on the log10 scale:")
print(f"{'':<34}{'high':>10}{'moderate':>12}")
print(f"{'built into the simulation':<34}{HIGH_LIFT:>10.3f}{MODERATE_LIFT:>12.3f}")
print(
    f"{'fitted, no floor or ceiling':<34}"
    f"{uncensored_high_gap:>10.3f}{uncensored_moderate_gap:>12.3f}"
)
print(
    f"{'fitted, as the laboratory reports':<34}{high_gap:>10.3f}{moderate_gap:>12.3f}"
)
print(
    f"\nThe floor and ceiling leave {attenuation:.0%} of the gap. The same shrinkage applies"
    "\nto the real data, so the paper's estimated differences between beaches are"
    "\nsmaller than the true ones, not larger."
)

pl.DataFrame(
    {
        "gap": [
            "Built into the simulation",
            "Estimated, without the floor and ceiling",
            "Estimated, with the floor and ceiling",
        ],
        "high": [HIGH_LIFT, uncensored_high_gap, high_gap],
        "moderate": [MODERATE_LIFT, uncensored_moderate_gap, moderate_gap],
    }
).write_csv(GAPS_PATH)
print(f"Saved the gaps to {GAPS_PATH}")

print("\nAdvice from yesterday's result:")
with pl.Config(tbl_rows=-1, tbl_hide_dataframe_shape=True):
    print(agreement.with_columns(pl.col("share").round(3)))

print("\nChecks:")
for description, passed, detail in checks:
    print(f"  {'pass' if passed else 'FAIL'}  {description} ({detail})")

failed = [description for description, passed, _ in checks if not passed]
if failed:
    raise SystemExit(
        "\nThe analysis did not recover what the simulation built in:\n  "
        + "\n  ".join(failed)
    )
print("\nThe analysis recovers what the simulation built in.")
