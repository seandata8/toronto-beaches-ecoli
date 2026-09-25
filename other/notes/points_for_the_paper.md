# Points the paper has to make

Things found while exploring that a reader would otherwise get wrong. Each one needs a sentence or two somewhere in the paper, not a section of its own.

The check of the analysis against the simulated data, and the shrinkage the reporting floor and ceiling cause, are in `method_validation.md`.

## Samples against days

The summary figure counts single samples; the analysis counts beach-days. These are different units and the paper should say so once, plainly, so the two figures do not look contradictory.

The gap between them is small, and that is itself worth reporting. Day counts are from `other/results/exceedance-by-beach.csv`; sample shares are from `data/02-analysis_data/analysis_data.csv` (checked 25 September 2026):

| Beach | Samples over 100 | Days over 100 | Days over the limit |
|---|---|---|---|
| Marie Curtis Park East | 35.4% | 34.1% | 657 of 1,925 |
| Sunnyside | 33.6% | 31.8% | 632 of 1,986 |
| Kew Balmy | 19.3% | 15.7% | 316 of 2,011 |
| Centre Island | 19.4% | 13.9% | 268 of 1,929 |
| Bluffer's | 12.9% | 11.3% | 226 of 2,001 |
| Ward's Island | 10.3% | 9.1% | 177 of 1,952 |
| Woodbine | 10.7% | 8.8% | 177 of 2,005 |
| Cherry | 8.9% | 7.4% | 148 of 2,003 |
| Hanlan's Point | 8.0% | 6.7% | 130 of 1,939 |
| Gibraltar Point | 5.9% | 4.4% | 85 of 1,911 |

Averaging five or six sites might have been expected to pull most days back under the limit. It does not: the day share sits 1.2 to 5.5 points below the sample share, never half. A beach's sites are highly correlated, so when one is dirty the others usually are too, and the geometric mean tracks the samples rather than smoothing them away. The gap is widest at two of the middle beaches, Centre Island (5.5 points) and Kew Balmy (3.6), and 1.2 to 1.9 points at the other eight.

## "Over the limit" is not "closed"

The dataset does not record whether a warning was ever posted. Every "warning day" in this paper is a rule applied after the fact: a daily geometric mean above 100 with at least four results. Three reasons to be careful with the wording:

- The City may post on a two-day geometric mean rather than one day's samples.
- Results take about 24 hours, so a posting reflects the previous day's water.
- Posting decisions may consider more than the number.

The paper should say "days over the limit" or "days exceeding the threshold", never "closures" or "days the beach was posted".

## Toronto's limit is stricter than the province's

Toronto uses 100 E. coli per 100 mL; Ontario and Health Canada use 200. A reader who knows the provincial figure will wonder why every line in the paper sits at 100, so the data section should give both numbers and say which one the paper uses.

## The reporting floor and ceiling

Covered in detail in `raw_data_findings.md`. The paper needs the short version: nothing is reported below 10, and from 2018 high readings are increasingly reported as exactly 1,000, with nothing above it in 2026. Both are properties of the laboratory's reporting, not of the water, and the ceiling understates how far the worst beaches sit above the rest.

The ceiling can also hide a day over the limit, which deserves one to three sentences, not more. Of 290 beach-days since 2018 with a result of exactly 1,000, 34 have a geometric mean below 100. On about 8 of them a true reading of 2,000 or less would have put the day over the limit, and on about 18 a reading of 5,000 or less would have. So the count of days over the limit after 2018 is, if anything, slightly low. Details are in `raw_data_findings.md`, under "Could the ceiling have hidden a warning?".

## The two mislabelled sites

`60W` and `GP6` appear in 2026 only and sit 14 to 16 km from the beaches they are listed under. They are dropped. One sentence in the cleaning appendix, with the distance, so the decision is checkable.

Add a footnote (or endnote) on the City's reply: on 25 September 2026 Toronto Public Health staff said the listing had been referred for correction (personal communication). Do not name the staff member. The footnote should also say the paper uses the data as downloaded on 22 September 2026, so a later fix on the portal does not change the results, and a fresh download may list these sites differently.

## Question 1: what the paper needs

Two figures carry the answer: every beach-day (`paper/figures/all-beach-days.png`) for the description, and the model estimates with 95% intervals (`paper/figures/beach-estimates.png`) for the test. The rest is three or four sentences of support, no extra figures or tables. Numbers checked 25 September 2026.

- **Not a few bad summers (one sentence).** Marie Curtis was over the limit on 22–60% of days depending on the season, and Sunnyside on 21–47%. In 19 of 20 seasons both were over the limit more often than every other beach; the exception is 2021, when Kew Balmy (26.9%) passed Sunnyside (24.8%). Source: `other/results/exceedance-by-beach-and-year.csv`.
- **Not the 1,000 ceiling (one clause, next to the ceiling sentences).** Splitting the record at 2018 leaves the ranking much the same: Marie Curtis 36.9% of days before and 31.0% from 2018, Sunnyside 31.8% both times, Gibraltar Point 5.0% and 3.8%. Printed by `scripts/07-analyse_data.py`.
- **Why days in a month are treated as related (a phrase in the method, not a result).** Days over the limit come in runs, so the standard errors treat days in the same calendar month as related. The supporting number (days over the limit vary 8.7 times as much as independent days would) belongs in an appendix or nowhere.
- **The gaps are understated (one sentence, also in the figure caption).** Because results are reported only between 10 and 1,000, the model's gaps come out at about 65% of their true size in the simulation; the direction is never reversed.
- **Pairwise tests (one sentence; the table in an appendix at most).** Marie Curtis and Sunnyside differ from every other beach but not from each other; 31 or 32 of the 45 pairs differ depending on how days are grouped, and most of the rest are among the lower beaches, too close to separate.
- **Model rank vs share of days.** Centre Island ranks above Kew Balmy in the model (1.22× against 1.09×) but below it in share of days over the limit (13.9% against 15.7%). The model compares typical levels on the same days; the share counts how often 100 is crossed. One sentence so a reader comparing the two figures is not confused.
