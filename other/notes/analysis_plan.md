# Analysis plan and simulation design

Written 22 September 2026, before any comparison of beaches in the real data. Background facts about the data are in `raw_data_findings.md`.

## Questions

1. **Main question: do some Toronto beaches have swimming warnings more often than others?** If so, suggest reasons from the literature and local geography, such as nearby rivers and creeks, storm-water outfalls, or currents.
2. **Supporting question: how well does one day's E. coli level predict the next day's?** Lab results take about 24 hours, so a warning posted today reflects yesterday's water. If levels change a lot from day to day, warnings based on yesterday's samples will often be wrong about today.
3. **Future work, not in this paper: can rainfall and wind predict warning days?** This needs weather data from another source and a predictive model.

## Definitions

- **Beach-day:** one beach on one sampling day.
- **Daily geometric mean:** the geometric mean of the E. coli results from a beach's sites on one day. The geometric mean is the average on a log scale, converted back. It is less affected by single very high values than the ordinary average. Only that day's samples are used, not a two-day average.
- **Minimum results:** the daily geometric mean is computed only when at least 4 results are available. Four, not five, so that Sunnyside, which had only four sites before 2026, is included.
- **Warning day:** a beach-day with a daily geometric mean above 100 E. coli per 100 mL (Toronto's standard).

## Data to analyse

- Seasons from about Victoria Day to Labour Day, 2007–2026. Dates outside this window are removed.
- Blank `eColi` rows are removed. They are days when no test was done.
- The value of 6,191,768 is removed as an error. It is about 60,000 times the warning level.
- Sites `60W` and `GP6` are left out, pending a reply from the City: they cover only 2026 and are far from their listed beaches.

## Question 1: comparing beaches

**Unit:** one beach in one month of one year (for example, Cherry Beach in July 2014). The outcome is the **share of sampled days that were warning days**. A share is used, not a count, because months have different numbers of sampling days.

**Months used:** June, July and August. May and September are only partly sampled.

**Test: two-way ANOVA with beach and month-year as factors.** ANOVA (analysis of variance) tests whether the average warning share differs between beaches by more than chance variation would produce. Month-year is included as a second factor because weather affects all beaches at once: a wet July raises warnings everywhere. Including it compares each beach with the others in the same month, so a beach is not judged "worse" just because of a rainy period.

**Follow-up: Tukey's test**, which compares every pair of beaches and says which pairs differ, while allowing for the fact that many pairs are being compared.

**Checks:** shares are bounded between 0 and 1 and often near 0, which can break ANOVA's assumption of roughly bell-shaped errors. Plot the residuals, meaning what the model does not explain. If they are far from bell-shaped, report that and consider a model for yes/no outcomes (logistic regression) instead.

**Reasons for differences (from literature, not tested):** for each beach, note nearby rivers and creeks, outfalls, and whether it is on the mainland or Toronto Island. These are hypotheses to discuss, not causes the data can prove.

## Question 2: day-to-day predictability

- For each beach, pair each day's log10 geometric mean with the previous sampling day's value. Plot today against yesterday with one point per beach-day, and report the correlation. A correlation near 1 means yesterday predicts today well; near 0 means it does not.
- **Warning agreement:** treat yesterday's result as the posted warning for today and count four outcomes:
  - warning both days (correct warning)
  - no warning either day (correct all-clear)
  - warning yesterday but not today (unneeded warning)
  - warning today but not yesterday (missed warning)

  This measures how often the one-day delay gives the wrong advice.

## Simulation design (`scripts/00-simulate_data.py`)

The simulation creates fake data with the same structure as the real data, with differences built in on purpose. Running the planned analysis on it checks that the code works and that the methods find the differences that were built in.

| Part | How it is generated |
|---|---|
| Seed | fixed, so the simulation gives the same data every run |
| Calendar | 2007–2026, daily from Victoria Day to Labour Day |
| Beaches and sites | the 10 real beach names; 5 sites each, 4 at Sunnyside |
| E. coli | built on a log10 scale as the sum of the four parts below, then converted back |
| – beach baseline | 6 beaches at a common level, 2 moderately higher, 2 much higher; beaches are assigned to groups at random using the seed |
| – city-wide daily effect | one value per day shared by all beaches (weather), which partly carries over to the next day |
| – beach daily effect | one value per beach per day, which also partly carries over to the next day |
| – site noise | independent for each sample |
| Lab reporting | rounded to multiples of 10; anything below 10 reported as 10 |
| Missing values | about 1% of samples blank at random, plus a few whole days blank at every beach |
| Extreme errors | none; the real data's one extreme value is removed in cleaning, so the simulation matches cleaned data |

**Carry-over:** each day's effect equals a fraction of the previous day's effect plus new random variation. The fraction sets how well one day predicts the next. For example, 0.5 means half of yesterday's deviation remains today.

**Starting values** (log10 scale, adjusted so that about half of simulated results equal 10, as in the real data):

| Setting | Value |
|---|---|
| Baselines | common 1.3; moderate +0.2; high +0.4 |
| City-wide daily effect | carry-over 0.5, spread (SD) 0.20 |
| Beach daily effect | carry-over 0.5, spread (SD) 0.25 |
| Site noise | spread (SD) 0.30 |

The beach groups are made up. They are not based on the real data.

**What the analysis should recover from the simulated data:**
- ANOVA finds a difference between beaches.
- Tukey's test separates the high beaches from the common ones and does not separate the six common beaches from each other, apart from occasional false positives.
- The day-to-day correlation matches what the carry-over settings imply.

## Tests

- `scripts/01-test_simulated_data.py` checks the simulated data.
- A later script checks the cleaned real data with the same checks where they apply:
  - column names and types
  - dates within each season
  - 10 beaches and the expected number of sites per beach
  - at most one row per site per day
  - E. coli values of 10 or more, in multiples of 10
  - share of blanks within a plausible range

## Open decisions

- Season window for the real data. The simulation uses Victoria Day to Labour Day; the City describes the season as June to Labour Day.
- How to treat results reported as 10, since the true value may be 10 or less.
- `60W` and `GP6`: drop or reassign, depending on the City's reply.