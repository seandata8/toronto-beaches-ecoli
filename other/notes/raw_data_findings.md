# Findings from the raw data

Summary of what `other/explore/raw_data_overview.ipynb` found in `data/01-raw_data/raw_data.csv`, downloaded 22 September 2026 from Open Data Toronto (package `toronto-beaches-water-quality`, resource "toronto-beaches-water-quality - 4326.csv"). Section names in brackets refer to the notebook.

## Structure

- 102,534 rows and 7 columns: `_id`, `beachId`, `beachName`, `siteName`, `collectionDate`, `eColi`, `geometry`. [Overview]
- One row is one sampling site on one day. No site has more than one row on the same day. [Sampling frequency]
- `_id` is a row number. `beachId` and `beachName` match one to one.
- `geometry` is a GeoJSON point with **longitude first, then latitude**. Map tools such as Google Maps expect latitude first. [`siteName` and `geometry`]

## Beaches and sites

- 10 beaches and 52 sites. Each site has one fixed location for its whole record. [Beaches and sites; `siteName` and `geometry`]
- Most beaches have 5 sites. Kew Balmy has 6. Sunnyside had only 4 (19W–22W) from 2007 to 2025. [Samples per beach per day]
- Two sites were added on 2026-05-19 and sampled daily after that: `60W` (listed as Sunnyside Beach) and `GP6` (listed as Gibraltar Point Beach). Both are about 14–16 km from the beaches they are listed under, in the east end between Kew Balmy and Bluffer's. All other sites are within 0.4 km of the rest of their beach. They may be mislabelled. An email to SwimSafe@toronto.ca on 22 September 2026 asked about them. On 25 September 2026 Toronto Public Health staff replied that the listing had been referred to their IT team for correction, expected the following week. The reply did not say whether the beach name, coordinates or site code is wrong. [Map of sampling sites]

## When sampling happens

- Dates run from 2007-06-03 to 2026-09-16, with 2,063 distinct sampling days. [When sampling happens]
- The City states that daily samples are collected "between June and September (Labour Day)" (*Beach Water Quality – City of Toronto*; *Toronto Beaches Water Quality* open data page). In the data, most seasons start in late May, around Victoria Day.
- Sampling is daily, including weekends: each day of the week has 292–299 sampling days. [Sampling frequency]
- In most years 95–100% of days between the first and last date were sampled. Exceptions: early one-off dates before the season (for example 2 March 2017 and 26 April 2024), days missed within the 2009 season (75 of 99), and a late start in 2020 (15 June). [Sampling frequency]
- Some rows fall after Labour Day, for example 2026-09-08 and 2026-09-16 (Labour Day 2026 was 7 September). These have no results and should be removed in cleaning.

## E. coli values

- Units are E. coli per 100 mL of water. [City of Toronto, *About Beach Water Quality*]
- 98,991 results. The median is 20 and the maximum is 6,191,768. Only one value is 100,000 or higher. [E. coli values]
- 48,488 results (49%) are exactly 10, and 99.9% are multiples of 10. So 10 appears to be the lowest reported value (a reporting floor), and values are reported in steps of 10. Only 63 results are below 10 and 132 are not multiples of 10. [E. coli values]
- Values are strongly right-skewed and span several orders of magnitude, so a log scale suits graphs and models. [E. coli values]
- 16,017 results (16%) are above 100.

## A reporting ceiling at 1,000, from 2018

Found on 23 September 2026 in the figure of every raw result (`paper/figures/all-raw-results.png`), which shows a dense bar sitting exactly on 1,000 in the later years.

| Period | Results reported as exactly 1,000 | Results above 1,000 |
|---|---|---|
| 2007–2017 | 0 to 0.2% a year | 39 to 133 a year |
| 2018–2025 | 1.0% to 2.3% a year | 10 to 42 a year |
| 2026 | 1.8% | none, out of 5,684 results |

Before 2018, 1,000 was an ordinary value and readings ran as high as 15,820. From 2018 the laboratory reports more and more high samples as exactly 1,000, and in 2026 nothing above 1,000 appears at all. This looks like a change in reporting practice rather than in the water: high results are being recorded as "1,000" rather than measured.

So the data is censored at both ends, 10 below and 1,000 above, and the ceiling arrived partway through the record.

**What this means for the analysis:**

- **Counting days above 100 is unaffected.** A censored value of 1,000 is ten times the threshold, so a day capped at 1,000 was over the threshold whatever its true value.
- **The model is affected slightly.** Beach coefficients come from mean log10 values, and capping the top squeezes those means, more so after 2018 and more so at the beaches with the most high days. It touches 1–2% of samples, so the effect is small, but it runs in a known direction: it understates how far the worst beaches sit above the rest.
- **Capped values stay in.** Dropping them would throw away the worst days, which is the opposite of what the question needs. The handling is to document the ceiling and report which way it biases the estimate.

### Could the ceiling have hidden a warning?

Checked on 25 September 2026 using `data/02-analysis_data/analysis_data.csv`. A warning depends on the beach's daily geometric mean, not on a single sample. So a capped 1,000 could hide a warning if the geomean with 1,000 in it is at or below 100 but the true value would have pushed it over.

- 290 beach-days from 2018 on have at least one result of exactly 1,000. On 256 of them the geomean is over 100 anyway. On 34 it is below 100 (none is exactly 100). Every one of the 34 has a single 1,000.
- For each of the 34, the true value needed to lift the geomean to 100 is x = 1000 × (100 / geomean)^n, where n is the number of samples that day. Raising the capped value can only raise the geomean.

| True value needed for a geomean of 100 | Beach-days |
|---|---|
| 2,000 or less | 8 |
| 5,000 or less | 18 |
| over 20,000 | 9 (the ceiling almost certainly made no difference) |

- The closest cases are Centre Island 2024-08-12 (about 1,130 needed), Centre Island 2025-08-22 (about 1,230), Marie Curtis 2023-08-25 (about 1,490), and Bluffer's 2020-06-15 and 2020-06-16 and Centre Island 2022-07-29 (about 1,670 each).
- Centre Island has 13 of the 34 days, Sunnyside and Kew Balmy 5 each, Bluffer's 4, Woodbine and Marie Curtis 3 each, and Hanlan's Point 1.

So the ceiling could have hidden a warning on a handful of days, roughly 8 to 18 over nine years, if the true reading was a few thousand. This changes the earlier point that counting days above 100 is unaffected: that holds for single samples, but not for the geomean-based warning.

Caveats:

- Values above 1,000 still appear every year from 2018 to 2025, so the ceiling is not applied to every sample. Some of these 1,000s may be real readings. Worth asking the City whether 1,000 is an upper reporting limit and when it applies.
- Bluffer's 2020-06-15 and 2020-06-16 have the same five values (20, 50, 50, 120, 1000). This looks like one day's results entered twice.

## Warning rule

- Toronto's standard is 100 E. coli per 100 mL. The provincial and federal standard is 200. [*About Beach Water Quality*]
- A swimming warning is posted when the geometric mean of a beach's samples (normally five) exceeds 100 (Sanchez et al. 2021; the 2023 PLOS ONE article on Woodbine Beach). One 2023 article on same-day qPCR testing refers to Toronto's "2-day E. coli geometric mean" posting decisions, so the exact rule is worth checking before relying on it.
- Results take about 24 hours from the lab, so a warning reflects the previous day's water. [*Beach Water Quality – City of Toronto*]

## Missing results

- 3,543 rows (3.5%) have a blank `eColi`. [Overview]
- The City says: "Occasionally TPH is not able to test the water quality due to circumstances such as adverse weather conditions." [*About Beach Water Quality*]
- The data keeps a row for every site even when no test was done, so blank rows are placeholders, not lost measurements.
- 672 of 20,462 beach-days have no results. On 23 dates no beach had results; most of these are early one-off dates before the season, and only three are mid-season (2020-07-16, 2026-07-17, 2026-07-18). On 73 dates only one beach had no results. [Days with no results]

## Samples per beach per day

- Sunnyside had exactly four results on 1,883 of its 2,061 beach-days, because it had only four sites before 2026. This is the sampling design, not missed samples. [Samples per beach per day]
- At the other nine beaches, a day with exactly four results happened only 55 times in total, usually because one of five samples was blank. [Samples per beach per day]

## For cleaning

- Keep only dates in the season (from about Victoria Day to Labour Day). This removes the early one-off dates and post-season placeholder rows.
- Drop rows with blank `eColi`.
- Drop `60W` and `GP6`. The City's reply confirmed a listing problem but did not name the right beach.
- Decide how to treat the value of 6,191,768, and whether results of 10 are treated as "10 or less".
- Parse `collectionDate` as a date and `geometry` into longitude and latitude columns.