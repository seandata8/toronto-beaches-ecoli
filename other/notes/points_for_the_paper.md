# Points the paper has to make

Things found while exploring that a reader would otherwise get wrong. Each one needs a sentence or two somewhere in the paper, not a section of its own.

## Samples against days

The summary figure counts single samples; the analysis counts beach-days. These are different units and the paper should say so once, plainly, so the two figures do not look contradictory.

The gap between them is small, and that is itself worth reporting:

| Beach | Samples over 100 | Days over 100 | Days over the limit |
|---|---|---|---|
| Marie Curtis Park East | 35.4% | 34.1% | 658 of 1,927 |
| Sunnyside | 33.7% | 31.9% | 636 of 1,993 |
| Kew Balmy | 19.3% | 15.7% | 319 of 2,030 |
| Centre Island | 19.4% | 13.9% | 268 of 1,930 |
| Bluffer's | 13.0% | 11.5% | 231 of 2,008 |
| Ward's Island | 10.3% | 9.1% | 177 of 1,953 |
| Woodbine | 10.8% | 8.8% | 179 of 2,024 |
| Cherry | 8.9% | 7.4% | 150 of 2,022 |
| Hanlan's Point | 8.1% | 6.8% | 131 of 1,940 |
| Gibraltar Point | 5.9% | 4.5% | 86 of 1,912 |

Averaging five or six sites might have been expected to pull most days back under the limit. It does not: the day share sits 1 to 5 points below the sample share, never half. A beach's sites are highly correlated, so when one is dirty the others usually are too, and the geometric mean tracks the samples rather than smoothing them away. The gap is widest at the middle beaches (Centre Island loses 5.5 points) and narrowest at the dirtiest.

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

## The two mislabelled sites

`60W` and `GP6` appear in 2026 only and sit 14 to 16 km from the beaches they are listed under. They are dropped, and an email to the City went unanswered. One sentence in the cleaning appendix, with the distance, so the decision is checkable.