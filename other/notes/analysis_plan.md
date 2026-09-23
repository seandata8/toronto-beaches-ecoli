# Analysis plan and simulation design

Written 22 September 2026, revised 23 September 2026, before any comparison of beaches in the real data. Background facts about the data are in `raw_data_findings.md`.

## Questions

1. **Main question: do some Toronto beaches have swimming warnings more often than others?** If so, suggest reasons from the literature and local geography, such as nearby rivers and creeks, storm-water outfalls, or currents.
2. **Supporting question: how well does one day's E. coli level predict the next day's?** Lab results take about 24 hours, so a warning posted today reflects yesterday's water. If levels change a lot from day to day, warnings based on yesterday's samples will often be wrong about today.
3. **Future work, not in this paper: can rainfall and wind predict warning days?** This needs weather data from another source and a predictive model.

## Describing versus inferring

Both questions are answered by description, not by statistical tests.

The dataset covers every Toronto beach across twenty seasons, so "which beaches exceeded the threshold most often?" and "how often did yesterday's result give the wrong advice about today?" are questions of arithmetic on a complete record. No assumptions are needed and no model is fitted. These descriptive answers are the findings of the paper and belong in the main text with the graphs.

Testing answers a different question: whether a gap between two beaches reflects a durable difference rather than the particular weather these twenty summers happened to bring. That is what the model section does, and it is reported after the descriptive results rather than in place of them.

One framing point that shapes the uncertainty. The ten beaches are the whole population, not a sample from a larger set, so nothing is being generalised to unobserved beaches. The only role of chance is which summers occurred. The right question is therefore "would a different run of summers have reordered these beaches?", which is why dependence across days matters more than sample size.

## Definitions

- **Beach-day:** one beach on one sampling day.
- **Daily geometric mean:** the geometric mean of the E. coli results from a beach's sites on one day. The geometric mean is the average on a log scale, converted back. It is less affected by single very high values than the ordinary average. Only that day's samples are used, not a two-day average.
- **Minimum results:** the daily geometric mean is computed only when at least 4 results are available. Four, not five, so that Sunnyside, which had only four sites before 2026, is included.
- **Warning day:** a beach-day with a daily geometric mean above 100 E. coli per 100 mL (Toronto's standard). Because the dataset does not record whether a warning was actually posted, this is a measure defined here, not the official record, and is reported as "days exceeding the threshold" rather than "days with a posted warning". Toronto's own posting rule may use a two-day window.
- **Floor value:** a result reported as 10. The laboratory filters a fixed volume of water, so a filter with no colonies cannot be reported as zero; it means "at or below the detection limit". About half of all results sit at this floor.

## Data to analyse

- **Seasons run from Victoria Day to Labour Day, 2007–2026.** Dates outside this window are removed. Checked against the data on 23 September 2026: from 2012 onward sampling starts the day after Victoria Day in 11 of 15 years, and the median start across all 20 years is Victoria Day plus one day, against 8.5 days before 1 June. Sampling begins the Tuesday after the holiday Monday. Cutting at 1 June instead would drop 7,284 results, about 7% of the record, including 8–13 sampling days a year at nearly every beach since 2012.
- Late May is cleaner than the rest of the season: 8.6% of its beach-days exceed 100, against 13–16% in June, July and August. Including it lowers every beach's overall share slightly. This affects all beaches alike, so it should not reorder them, but the paper says so. Note also that 2007 and 2008 have no late-May sampling and 2020 started in mid-June; by-season shares handle this, because each season is summarised on its own days.
- Blank `eColi` rows are removed. They are days when no test was done.
- The value of 6,191,768 is removed as an error. It is about 60,000 times the warning level.
- Sites `60W` and `GP6` are left out, pending a reply from the City: they cover only 2026 and are far from their listed beaches.

## Question 1: comparing beaches

**Main result (descriptive).** For each beach, the share of sampled days that exceeded the threshold, over the whole record and by season. Shares are used rather than counts because beaches and seasons differ in how many days were sampled. This is reported alongside a graph of every beach-day, so the reader sees the actual observations and not only the summary.

**Why rain is not a confounder.** A confounder would make one beach look worse than another when it is not. Rain falls on all the beaches on the same days, and over twenty seasons each beach experiences much the same weather, so it cannot manufacture a ranking. If beaches near river mouths respond more strongly to rain, that responsiveness is part of what makes them worse, not a distortion. Shared weather affects the uncertainty around the shares, not the shares themselves.

**Why the counts are not Poisson.** Warning days are a count out of a known number of sampled days, so each sampled day is a yes/no trial and the natural description is binomial. Poisson approximates the binomial only when the probability is small, which fails for the frequently posted beaches that matter most here. Both distributions also assume days are independent at a constant rate, whereas a wet week posts a beach for several days running. The result is more variation across seasons than either distribution predicts, so fitted standard errors would be too small. Check this directly: count exceedance days per beach per season and compare the variance across seasons with the mean. Roughly equal supports Poisson; a variance several times the mean confirms the clustering.

### Model: same-day comparison between beaches

This is the paper's model section, reported in the main text after the descriptive shares. It answers a narrower question than the shares do: **when the same day's weather is held fixed, does one beach run higher than another, and by how much?**

**Form.** A linear model of the log10 daily geometric mean on beach and on date:

```
log10(daily geometric mean) ~ beach + date
```

with date as a factor, one level per sampling day. A date factor subtracts each day's city-wide average, so every beach is compared only with the other beaches sampled that same day. This is the paired same-day difference, fitted for all ten beaches at once instead of 45 separate pairings, and it is why rain is not a confounder here: a wet day raises that day's term, not any beach's term. Each beach's coefficient is its average log10 gap from the reference beach; because the outcome is on a log scale, 0.3 means about twice as high. Pairwise comparisons are contrasts between beach coefficients.

Three complications, each with a handling:

- **Days are not independent.** Levels carry over from one day to the next, so the standard errors the model reports are too small. Cluster by month-year, or block-bootstrap whole seasons, or thin to one day per week and check whether the conclusion survives.
- **Forty-five pairs.** With ten beaches, correct the pairwise contrasts for multiple comparisons using Holm or Tukey.
- **The floor.** The outcome is censored from below: 22% of beach-days have every sample at the detection limit, so their geometric mean is exactly 10 whatever the true level was. This is uneven across beaches, from 3.8% of days at Sunnyside to 33% at Hanlan's Point, so it shrinks the apparent gaps between the cleanest beaches most. Refit on days where at least one of the two beaches is above the floor, and report the censoring share per beach beside the coefficients so the reader can see where the estimate is weakest.

**Site counts differ between beaches.** Sunnyside has 4 sites, Kew Balmy 6, the rest 5. A mean of 4 samples is noisier than one of 6, and because exceedance means crossing a fixed threshold, extra noise pushes more days over 100 even when the true level is identical. Sunnyside is therefore mildly favoured to look worse and Kew Balmy to look better, from site counts alone. The size of this effect is measured on the simulated data, where the site counts differ but the baselines do not, and the measured size is reported with the descriptive shares.

**Reasons for differences (from literature, not tested):** for each beach, note nearby rivers and creeks, outfalls, and whether it is on the mainland or Toronto Island. These are hypotheses to discuss, not causes the data can prove.

## Question 2: day-to-day predictability

**Pairing rule.** A pair is two beach-days at the same beach on consecutive calendar days, both with a daily geometric mean. Days either side of a gap are not paired, because advice carried over a three-day gap is not the process being described. This costs few pairs: the gaps are the missed days within the 2009 season, the mid-season days with no results anywhere (2020-07-16, 2026-07-17, 2026-07-18), and season boundaries. The same rule applies to both parts below.

- **Warning agreement (main result).** Treat yesterday's result as the advice given for today and count four outcomes:
  - warning both days (correct warning)
  - no warning either day (correct all-clear)
  - warning yesterday but not today (unneeded warning)
  - warning today but not yesterday (missed warning)

  This is a count, not a model, and it depends only on whether each day crossed 100, so the detection floor does not affect it. It is the strongest finding available from these data because it rests on no assumptions.

- **Correlation (supporting).** For each beach, pair each day's log10 geometric mean with the previous day's value. Plot today against yesterday with one point per beach-day and report the correlation. Because about half of all results are at the floor, many pairs have both days censored and agree perfectly by construction, which inflates the correlation without showing predictability. Report the correlation twice: over all pairs, and over pairs where at least one of the two days is above the floor.

## Censoring check

Recompute the headline numbers with floor values set to 5 rather than 10, the common convention of substituting half the detection limit, and state whether the conclusions change. One paragraph in an appendix.

## Simulation design (`scripts/00-simulate_data.py`)

The simulation creates fake data with the same structure as the real data, with differences built in on purpose. Running the planned analysis on it checks that the code works and that the methods find the differences that were built in.

| Part | How it is generated |
|---|---|
| Seed | fixed, so the simulation gives the same data every run |
| Calendar | 2007–2026, daily from Victoria Day to Labour Day |
| Beaches and sites | the 10 real beach names; 5 sites each, except 6 at Kew Balmy and 4 at Sunnyside, as in the real data before 2026 |
| E. coli | built on a log10 scale as the sum of the four parts below, then converted back |
| – beach baseline | 6 beaches at a common level, 2 moderately higher, 2 much higher. Sunnyside (4 sites) and Kew Balmy (6 sites) are put in the common group on purpose, so that their exceedance shares measure the site-count effect on its own; the remaining beaches are assigned to groups at random using the seed |
| – city-wide daily effect | one value per day shared by all beaches (weather), which partly carries over to the next day |
| – beach daily effect | one value per beach per day, which also partly carries over to the next day |
| – site noise | independent for each sample |
| Lab reporting | rounded to multiples of 10; anything below 10 reported as 10 |
| Missing values | 3.2% of beach-days blank as a whole, 0.2% of single samples blank, and 3 days with no results at any beach. In the real data 95% of blanks are whole beach-days (672 of 20,462), and only 128 beach-days are partly blank, so scattering blanks across single samples would be wrong: it would knock four-site Sunnyside below the four-result minimum far more often than really happens |
| Extreme errors | none; the real data's one extreme value is removed in cleaning, so the simulation matches cleaned data |

**Carry-over:** each day's effect equals a fraction of the previous day's effect plus new random variation. The fraction sets how well one day predicts the next. For example, 0.5 means half of yesterday's deviation remains today.

**Values used** (log10 scale, tuned on 23 September 2026 so that the share of results at the detection limit, the exceedance shares and the spread between beaches resemble the real data). Each spread is the standard deviation of that part once the carry-over has settled, so the four parts add up as squares and changing a carry-over alters persistence without widening the series.

| Setting | Starting value | Value used |
|---|---|---|
| Baselines | common 1.3; moderate +0.2; high +0.4 | common 1.10; moderate +0.2; high +0.4 |
| City-wide daily effect | carry-over 0.5, spread (SD) 0.20 | carry-over 0.5, spread (SD) 0.30 |
| Beach daily effect | carry-over 0.5, spread (SD) 0.25 | carry-over 0.5, spread (SD) 0.34 |
| Site noise | spread (SD) 0.30 | spread (SD) 0.50 |

The starting values put too little spread on a single sample, which left only about a quarter of results at the detection limit and almost no exceedance days. The values used give 47% of results at the limit against 49% in the real data, 3.6% blank against 3.5%, and exceedance shares from 3.4% to 17% against 4.5% to 34%. The simulated beaches are closer together than the real ones because the built-in lifts of +0.2 and +0.4 are modest; that is a choice, not a failure to match.

**Carry-over across seasons:** the carry-over runs within a season only. Each season starts with a fresh draw, because there is no water quality record over the winter to carry.

The beach groups are made up. They are not based on the real data.

**What the analysis should recover from the simulated data:**
- The exceedance shares rank the beaches in the order built in, with the two high beaches clearly above the rest.
- The model's beach coefficients recover the built-in baselines: about +0.2 for the moderate beaches and +0.4 for the high ones, relative to the common group.
- The pairwise contrasts separate the high beaches from the common ones and do not separate the six common beaches from each other, apart from occasional false positives.
- Over several seeds, pairs of the six common beaches are called different about 5% of the time. A much higher rate means the built-in day-to-day carry-over is breaking the assumption that days are independent, and the clustering or block-bootstrap fix applies to the real data too.
- The beaches with 4 and 6 sites have the same baseline as the other common beaches, so any difference in their exceedance shares measures the site-count effect alone. That measured size is what the real data's Sunnyside and Kew Balmy shares are read against.
- Exceedance days per beach per season vary more than a Poisson distribution predicts, and the excess grows as the carry-over fraction is raised. Since the simulation knows the true carry-over, this calibrates how much of the real data's excess variation is explained by day-to-day persistence.
- The day-to-day correlation matches what the carry-over settings imply, and the correlation computed only on uncensored pairs is lower than the one computed on all pairs.

## Tests

- `scripts/01-test_simulated_data.py` checks the simulated data.
- A later script checks the cleaned real data with the same checks where they apply:
  - column names and types
  - dates within each season
  - 10 beaches and the expected number of sites per beach
  - at most one row per site per day
  - E. coli values of 10 or more, in multiples of 10
  - share of blanks within a plausible range
  - share of results at the floor near one half

## Open decisions

- Whether to report the floor sensitivity check in the appendix or only mention its outcome in a sentence.
- `60W` and `GP6`: drop or reassign, depending on the City's reply.
