# Results

Produced 23 September 2026 by `scripts/07-analyse_data.py`, using the functions checked against simulated data first (`method_validation.md`). Tables are saved in `other/results/`.

19,662 beach-days, 2007 to 2026.

## Executive summary

**Which beach you choose matters far more than which day you go.**

Two beaches are in a class of their own. Marie Curtis Park East was over Toronto's limit on 34.1% of its sampled days and Sunnyside on 31.8%, against 4.4% at Gibraltar Point: roughly eight times as often. Both sit 0.34 above the daily average on the log10 scale, meaning more than twice the E. coli of the average beach on the same day. They cannot be told apart from each other, and every other beach is clearly below them. Of the 45 pairs of beaches, 32 differ after correcting for the number of comparisons.

The ranking survives every check. Across years the two dirtiest beaches range from 22% to 60% and from 21% to 47% of days, and in 19 of the 20 years both were over the limit more often than every other beach; the exception is 2021, when Kew Balmy (26.9%) passed Sunnyside (24.8%). Splitting the record at 2018, when the reporting ceiling appeared, barely moves the numbers. And because the laboratory's floor and ceiling shrink differences by about a third, the true gaps are wider than these figures say.

Against that, the daily warning is a weak guide. Results take about a day, so a posting describes yesterday's water. It is better than nothing: a day after one over the limit is over the limit 37% of the time, against 10% after a day under it and 14% on any day. But of the days actually over the limit, 63% were not caught, and of the warnings that would be posted, 63% were unnecessary. One day's reading explains about 14% of the variation in the next.

So a swimmer is better served by knowing which beach they are standing on than by yesterday's reading of it.

Three caveats travel with these numbers: they are days over the limit as computed here rather than recorded closures, the estimated gaps are floors rather than best guesses, and consecutive days are related, which is why the uncertainty treats days in the same month as related rather than treating every day as independent.

## Question 1: some beaches go over the limit far more often than others

| Beach | Days over the limit | Share | Model estimate (log10) |
|---|---|---|---|
| Marie Curtis Park East | 657 of 1,925 | 34.1% | +0.341 |
| Sunnyside | 632 of 1,986 | 31.8% | +0.341 |
| Kew Balmy | 316 of 2,011 | 15.7% | +0.036 |
| Centre Island | 268 of 1,929 | 13.9% | +0.086 |
| Bluffer's | 226 of 2,001 | 11.3% | −0.080 |
| Ward's Island | 177 of 1,952 | 9.1% | −0.119 |
| Woodbine | 177 of 2,005 | 8.8% | −0.121 |
| Cherry | 148 of 2,003 | 7.4% | −0.147 |
| Hanlan's Point | 130 of 1,939 | 6.7% | −0.155 |
| Gibraltar Point | 85 of 1,911 | 4.4% | −0.178 |

**Marie Curtis Park East and Sunnyside are in a class of their own.** Both sit 0.34 above the daily average on the log10 scale, more than twice as high as the average beach on the same day, and they cannot be told apart from each other (difference 0.000, p = 0.99). Every other beach is clearly below them. Gibraltar Point is the cleanest.

**32 of the 45 pairs differ** after Holm's correction. The 13 that cannot be separated are mostly the middle and lower group, where the gaps are 0.01 to 0.06 on the log10 scale.

**Check on the monthly grouping (25 September 2026; `scripts/07-analyse_data.py`, saved as `other/results/beach-pairwise-grouping-check.csv`).** The standard errors group days by calendar month, and the partial months at each end of the season (late May, early September) make small groups. Merging them into their neighbours (late May into June, early September into August) cuts the groups from 96 to 60 and changes the standard errors by −4% to +18% (median +6%). One pair changes: Bluffer's against Cherry goes from Holm-corrected p = 0.033 to 0.061, so 31 pairs differ instead of 32. Every other conclusion is unchanged, including the two worst beaches differing from all eight others. Bluffer's against Cherry is borderline and should not be relied on; the paper can say "31 or 32 of the 45 pairs, depending on how days are grouped", or simply "most pairs".

**The ranking is not an artefact of a few years.** Marie Curtis ranges from 22% to 60% of days across years and Sunnyside from 21% to 47%. In 19 of the 20 years both were over the limit more often than every other beach. The exception is 2021, when Kew Balmy (26.9%) passed Sunnyside (24.8%). (An earlier version of this note said the cleanest beaches never exceeded 12% and the groups never overlapped; that was wrong. Only Gibraltar Point and Hanlan's Point stay near 12% (10.6% and 12.4% at most), and the other six middle and lower beaches reach 16–27% in their worst years. Checked 25 September 2026 against `other/results/exceedance-by-beach-and-year.csv`.)

**Nor is it an artefact of the reporting ceiling.** Splitting at 2018, when the ceiling appeared, leaves the ranking essentially unchanged: Marie Curtis 36.9% before and 31.0% after, Gibraltar Point 5.0% and 3.8%.

**The gaps are understated.** The simulation showed the reporting floor and ceiling leave about 65% of a true gap, so the real differences between beaches are larger than these numbers say. The direction is never reversed.

**Consecutive days are related, so the standard errors group days by calendar month.** A wet week raises a beach for several days running: one day's level correlates with the next at 0.42 (Question 2). Fitting the same model with every day treated as independent gives standard errors 1.3 to 2.3 times smaller (median 1.9; `other/results/beach-model-standard-errors.csv`). So the grouping roughly doubles the width of the intervals, and the data carry about as much information as a quarter as many independent days. Ignoring it would make the p-values far too small.

(An earlier version of this note used a Poisson check instead: days over the limit per beach per year had a variance 8.7 times their mean. That number pooled all ten beaches, so it mostly measured the differences between beaches, not runs of days; within single beaches the ratio is 1.2 to 4.8, and it also mixes wet years with dry ones. It was replaced on 25 September 2026.)

## Question 2: yesterday's result is a weak guide to today

Lab results take about 24 hours, so a posted warning reflects the previous day's water. Over 18,998 consecutive-day pairs:

| Outcome | Days | Share |
|---|---|---|
| Correct all-clear | 14,584 | 76.8% |
| Correct warning | 1,002 | 5.3% |
| Unneeded warning | 1,712 | 9.0% |
| Missed warning | 1,700 | 8.9% |

**Two thirds of the days that were actually over the limit were not caught**: of 2,702 such days, yesterday's result flagged 1,002, or 37%.

**Two thirds of the warnings would have been unnecessary**: of 2,714 warnings yesterday's result would post, 1,002 were needed, again 37%.

The symmetry is not a coincidence — over a long record the number of days entering and leaving the over-limit state must balance.

**The warning still carries information.** Against a base rate of 14% (2,702 of 18,998 days over the limit), a day after one over the limit is over it 37% of the time (1,002 of 2,714), and a day after one under the limit only 10% of the time (1,700 of 16,284). A warning day is therefore about 3.5 times as likely to be over the limit as a day without one. It is not a coin toss; it is a weak signal that misses most dirty days and flags many clean ones.

The correlation between one day's log10 geometric mean and the next is **0.424**, falling to **0.372** when pairs with both days at the reporting floor are dropped. Squaring the latter, one day explains about 14% of the variation in the next. Water quality changes faster than the testing can follow, but not so fast that yesterday says nothing.

## What this means

The two findings pull in different directions, and the paper should say so:

- Where you swim matters a great deal. Marie Curtis Park East and Sunnyside are over the limit roughly eight times as often as Gibraltar Point, and that holds across twenty years.
- Today's posting is a weaker guide than swimmers likely assume. The delay between sampling and posting means a warning describes yesterday: it makes a dirty day about 3.5 times as likely, but it misses most dirty days and most warnings turn out unnecessary.

A swimmer is better served by knowing which beach they are at than by yesterday's reading of the one they chose.

## Caveats to carry into the paper

- These are days over Toronto's limit as computed here, not recorded closures. The data does not say whether a warning was posted, and the City may use a two-day mean.
- The 0.34 coefficients are floors, because of the censoring.
- Sunnyside has four sites where others have five or six, which adds noise to its daily mean and slightly favours it crossing the limit. The simulation put that effect at well under one percentage point, far too small to explain a 32% share.