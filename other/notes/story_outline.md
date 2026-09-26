# Story Outline

One bullet per paragraph. Figures and tables are placed at the paragraph that first discusses them.

## Introduction
- Why *E. coli* is measured at beaches: a sign of faecal pollution and a health risk; Toronto samples its ten beaches daily in summer and posts a warning above 100 per 100 mL (already written in part)
- The two questions (do some beaches go over the limit more often; how well does yesterday's result predict today's) and the gap: no published comparison of the beaches over 20 years, and no check of the one-day delay
- What was done and found, with numbers: 34% and 32% of days at Marie Curtis Park East and Sunnyside against 4% at Gibraltar Point; a warning based on yesterday catches 37% of the days over the limit
- Why it matters: which beach matters more than which day, and the posting is a weak guide
- Roadmap of the sections

## Data

### Source and context
- Where the data come from: the sampling program, daily sampling at four to six sites, warnings, published on Open Data Toronto (written)
- Toronto's limit of 100 against Ontario and Health Canada's 200, and which the paper uses (written)
- Ethics (no personal data; the stakes are the advice to swimmers) and similar datasets and why not used (written)

### Measurement
- The columns and how each is measured: beach, site and location (Figure 1, map), date, and the *E. coli* result from sample to laboratory count; results take about a day; blank rows when no sample could be taken
- The reporting floor at 10 and the ceiling at 1,000 from 2018 (Figure 2, all raw results)
- Cleaning, one sentence per removal: the implausible reading (ringed in Figure 2), the two sites far from their beaches (Figure 1), dates outside the season; details in the appendix; what remains (98,370 results, 50 sites, 2,019 days)
- Summary statistics per beach (Table 1)

### Methods
- Beach-days: the geometric mean in plain words, days with at least four results (19,662 beach-days); "over the limit" is computed, not a record of a posted warning
- The model: same-day comparison between beaches, days in the same month treated as related, what a 95% interval means in plain words, correction for comparing 45 pairs
- Consecutive days: how days are paired, and what the confusion matrix shows

## Results
- How often each beach goes over the limit (Figure 3, beach-day histogram); the ranking holds in 19 of 20 years and on both sides of the 2018 ceiling
- The same-day comparison with 95% intervals (Figure 4, beach estimates): Marie Curtis and Sunnyside differ from every other beach but not from each other; the reporting limits make the gaps look smaller than they are (about 65% of true size in simulation)
- Consecutive days (Table 2, confusion matrix): a warning based on yesterday catches 37% of days over the limit, and 37% of such warnings are needed; a day after one over the limit is 3.5 times as likely to be over it

## Discussion
- Brief summary of the data and results
- Why some beaches are worse than others (Etobicoke Creek, Humber River, storm-water outfalls, island against mainland beaches) and analyses of the data that could test these
- The current testing misses most bad days and posts unnecessary warnings most of the time; how it could be improved: a prediction model based on weather, qPCR for same-day testing
- Weaknesses: days computed, not recorded postings; floor and ceiling understate the gaps; no weather data; Sunnyside has four sites
- Next step: compare with the City's "Beach Condition Data for Researchers" download, which may record actual postings

## Appendix
- A. Data cleaning: every removal with counts and reasons, including the footnote on the City's reply about sites 60W and GP6
- B. (optional) Checking the method on simulated data
- C. (optional) Table of pairwise comparisons between beaches

## References
