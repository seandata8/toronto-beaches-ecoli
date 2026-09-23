# Results

Produced 23 September 2026 by `scripts/07-analyse_data.py`, using the functions checked against simulated data first (`method_validation.md`). Tables are saved in `other/results/`.

19,662 beach-days, 2007 to 2026.

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

**The ranking is not an artefact of a few summers.** Marie Curtis ranges from 22% to 60% of days across seasons and Sunnyside from 21% to 47%, while the cleanest beaches never exceed 12% in any season. The two groups do not overlap in any year.

**Nor is it an artefact of the reporting ceiling.** Splitting at 2018, when the ceiling appeared, leaves the ranking essentially unchanged: Marie Curtis 36.9% before and 31.0% after, Gibraltar Point 5.0% and 3.8%.

**The gaps are understated.** The simulation showed the reporting floor and ceiling leave about 65% of a true gap, so the real differences between beaches are larger than these numbers say. The direction is never reversed.

**Days over the limit cluster heavily**: their variance across beach-seasons is 8.7 times the mean, where a Poisson distribution would give 1. A wet week posts a beach for several days running, so counting days as independent trials would understate the uncertainty badly. This is why the model's standard errors are clustered by month.

## Question 2: yesterday's result is a poor guide to today

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

The correlation between one day's log10 geometric mean and the next is **0.424**, falling to **0.372** when pairs with both days at the reporting floor are dropped. Squaring the latter, one day explains about 14% of the variation in the next. Water quality changes faster than the testing can follow.

## What this means

The two findings pull in different directions, and the paper should say so:

- Where you swim matters a great deal. Marie Curtis Park East and Sunnyside are over the limit roughly eight times as often as Gibraltar Point, and that holds across twenty seasons.
- Whether today's posting is right is closer to a coin toss than swimmers likely assume. The delay between sampling and posting means a warning describes yesterday.

A swimmer is better served by knowing which beach they are at than by yesterday's reading of the one they chose.

## Caveats to carry into the paper

- These are days over Toronto's limit as computed here, not recorded closures. The data does not say whether a warning was posted, and the City may use a two-day mean.
- The 0.34 coefficients are floors, because of the censoring.
- Sunnyside has four sites where others have five or six, which adds noise to its daily mean and slightly favours it crossing the limit. The simulation put that effect at well under one percentage point, far too small to explain a 32% share.