# Checking the analysis against a known answer

Written 23 September 2026, before the analysis was run on the real data.

The simulation builds in a known answer: two beaches sit 0.4 higher on the log10 scale, two sit 0.2 higher, and the other six are level with one another. `scripts/06-validate_on_simulated_data.py` runs the paper's analysis on that data and checks it finds that pattern and no more. Both it and the real analysis call the same functions in `src/toronto_beaches_ecoli/analysis.py`, so the two cannot drift apart.

This belongs in the paper as a short methods paragraph and, if there is room, an appendix table. It is the evidence that the numbers in the results section come from code that works.

## What the check covers

All ten checks pass. In plain terms:

- The two beaches built dirtiest come out with the largest shares of days over the limit.
- The model recovers the built-in gaps almost exactly once the laboratory's reporting is taken away: 0.399 against a true 0.400, and 0.208 against a true 0.200.
- Every one of the 12 comparisons between a high beach and a level one is found.
- **None** of the 15 comparisons between beaches built at the same level is wrongly called a difference, so Holm's correction is not firing too often.
- Grouping days by month widens the standard errors by a median of 1.31 times, as the built-in carry-over implies. (This replaced a Poisson check on 25 September 2026; the old check pooled beaches built at different levels, so it measured their differences as much as any clustering. The real data give 1.90, so real days are more closely related than the simulation assumes.)
- Consecutive days correlate at 0.394, and the correlation falls to 0.368 when pairs with both days at the reporting floor are dropped, as predicted.

## The finding the paper has to report: censoring shrinks the gaps

The laboratory reports nothing below 10, rounds to multiples of 10, and from 2018 reports high readings as exactly 1,000. Running the analysis on the simulated data with and without that reporting gives:

| | Gap of the high beaches | Gap of the moderate beaches |
|---|---|---|
| Built into the simulation | 0.400 | 0.200 |
| Fitted, no floor or ceiling | 0.399 | 0.208 |
| Fitted, as the laboratory reports it | 0.260 | 0.126 |

**About 65% of the true gap survives the censoring.** The ranking of the beaches is unharmed and the direction is never reversed, but the size of every difference the paper reports is an underestimate. A reader should treat the estimated gaps as a floor.

This is worth stating plainly because it cannot be shown from the real data: only a simulation, where the true value is known, can measure how much the reporting takes away. To make it reproducible, `scripts/00-simulate_data.py` writes a second file, `data/00-simulated_data/simulated_data_uncensored.csv`, holding the same draws with the same blanks but without the floor, the rounding or the ceiling. Nothing but this check reads it.

## How the model works, in words for the paper

The model compares beaches on days when they were sampled together. For each day, the average across all beaches sampled that day is subtracted, which is what putting a term for every date in the model would do. What is left is how far each beach sat above or below the other beaches **that same day**, so a wet week raises nobody's estimate and rain cannot make one beach look worse than another.

Each beach's coefficient is its average gap from the others on the log10 scale, so 0.3 means about twice as high. Standard errors are clustered by calendar month (for example July 2019), because levels carry over from one day to the next and a month's sampled days are not independent trials. The 45 pairwise comparisons are corrected by Holm's method, which raises the bar each test has to clear so that the chance of any false difference across the whole family stays near 5%.

One caveat for honesty: subtracting each day's average uses up information that the count of rows does not know about, so the reported degrees of freedom are slightly optimistic. With about a hundred clusters (100 in the simulated data, 96 in the real data) the effect on the intervals is small.

## Software to cite

`statsmodels` for the model and Holm's correction, `pyarrow` (Polars uses it to hand data to statsmodels), alongside Python, Polars, numpy, matplotlib and pointblank.