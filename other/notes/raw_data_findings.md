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
- Two sites were added on 2026-05-19 and sampled daily after that: `60W` (listed as Sunnyside Beach) and `GP6` (listed as Gibraltar Point Beach). Both are about 14–16 km from the beaches they are listed under, in the east end between Kew Balmy and Bluffer's. All other sites are within 0.4 km of the rest of their beach. They may be mislabelled. An email to SwimSafe@toronto.ca was drafted to ask. [Map of sampling sites]

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
- Decide how to handle `60W` and `GP6` (drop or reassign), depending on any reply from the City.
- Decide how to treat the value of 6,191,768, and whether results of 10 are treated as "10 or less".
- Parse `collectionDate` as a date and `geometry` into longitude and latitude columns.