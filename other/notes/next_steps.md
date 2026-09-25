# Where the work stands, and what comes next

Written 24 September 2026, at the end of the session that cleaned the data and ran the analysis.

## Done

| Script | What it does |
|---|---|
| `00-simulate_data.py` | Simulated data with the reporting floor, the 2018 ceiling, blanks and known beach differences. Also writes the uncensored values |
| `01-test_simulated_data.py` | 16 pointblank checks on the simulated data |
| `02-download_data.py` | Raw data from Open Data Toronto |
| `03-clean_data.py` | 98,370 rows of analysis data |
| `04-test_analysis_data.py` | 22 pointblank checks on the cleaned data |
| `05-exploratory_data_analysis.py` | Four figures (site map and three data figures), written to `paper/figures/` |
| `06-validate_on_simulated_data.py` | Runs the analysis where the answer is known; all ten checks pass |
| `07-analyse_data.py` | The analysis of the real data; tables in `other/results/` |

The analysis itself lives in `src/toronto_beaches_ecoli/analysis.py`, so the check against simulated data and the real analysis call the same functions.

Findings are in `results_summary.md`, with the method check in `method_validation.md` and the things a reader could misread in `points_for_the_paper.md`.

## Next: `paper/paper.qmd`

**The figure code has to be refactored first.** `scripts/05-exploratory_data_analysis.py` runs top to bottom and saves PNGs. The paper must build its figures rather than read saved images, so the plotting has to become functions the paper can call, most likely in `src/toronto_beaches_ecoli/figures.py` alongside the analysis module. Two things follow from that:

- Each figure needs its title and subtitle to be optional. In the paper the words go in the Quarto caption under the figure, so having them drawn into the image as well would print them twice.
- The exploratory script then becomes a thin caller of those functions, or goes away.

**Captions.** In `paper.qmd` a figure is a code chunk with `#| label: fig-something` and `#| fig-cap: "..."`, which numbers it and puts the caption underneath. Writing `@fig-something` in the text gives "Figure 1". To get "Figure 1." rather than "Figure 1:", set `crossref: title-delim: "."` in the YAML header, and check it renders as expected the first time.

**Sections the paper needs:** title, author, date, abstract, introduction, data, model, results, discussion, references. The executive summary in `results_summary.md` is written to feed the abstract and introduction.

**References.** Python, Polars, numpy, matplotlib, pointblank, statsmodels, pyarrow, Quarto, the dataset itself and the Open Data Toronto portal, plus the literature in `other/literature/`. BibTeX.

## Smaller things still open

- The R scripts from the starter folder are superseded by the Python ones and can go: `00-simulate_data.R` through `06-model_data.R`, and `07-replications.R`.
- `data/00-simulated_data/simulated_data_uncensored.csv` is read only by `06-validate_on_simulated_data.py`. It is committed so the censoring check is reproducible.
- A sketches folder is expected in the repo and does not exist yet.
- The README still describes the starter template rather than this project.
- The City replied on 25 September 2026 about sites `60W` and `GP6`: Toronto Public Health staff referred the listing to their IT team for correction, expected the following week, without saying which field is wrong. The sites stay dropped, as recorded in the cleaning script and in `raw_data_findings.md`. The saved raw data is unaffected by any later fix.
## Open items from writing the paper (25 September 2026)

- **Claims to check against the sources:** Saleem et al. (2023) for Toronto posting on a two-day geometric mean; Sanchez et al. (2021) for E. coli as a sign of faecal pollution and for the 2012 federal limit of 200.
- **Final pass, layout:** the beach summary table splits across two pages, and the large figures each float onto their own page. Fix once all text is in.
- **Next steps in the paper, not this paper:** the City's "Beach Condition Data for Researchers" download (JSON, linked from the Beach Water Quality page) may record the warnings actually posted. Comparing it with the computed days over the limit would test the "over the limit is not posted" caveat. Left out to keep the paper short.
