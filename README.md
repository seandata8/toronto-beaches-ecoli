# Twenty Years of *E. coli* at Toronto's Beaches

## Overview

Toronto Public Health samples the water at the city's ten supervised beaches every day of the summer and posts a warning when *E. coli* exceeds 100 per 100 mL. This repo analyses every result the City has published, from 2007 to 2026, to answer two questions: are some beaches over the limit much more often than others, and how often does the sign posted each day, which is based on the previous day's samples, match the water quality on the day it is posted?

Two beaches, Marie Curtis Park East and Sunnyside, were over the limit on about a third of sampled days, more than seven times as often as the cleanest beach, while the daily sign missed nearly two thirds of the days over the limit.

The paper is `paper/paper.pdf`.

The data are the [Toronto Beaches Water Quality](https://open.toronto.ca/dataset/toronto-beaches-water-quality/) dataset from Open Data Toronto (package `toronto-beaches-water-quality`), published by Toronto Public Health.

## File structure

- `data/00-simulated_data/` contains the simulated data used to test the scripts and the analysis, with and without the laboratory's reporting floor and ceiling.
- `data/01-raw_data/` contains the raw data as downloaded from Open Data Toronto on 22 September 2026.
- `data/02-analysis_data/` contains the cleaned data used in the paper.
- `scripts/` contains the Python scripts that simulate, download, test, clean and analyse the data, numbered in the order they run.
- `src/toronto_beaches_ecoli/` contains the analysis functions, shared by the check on simulated data and the analysis of the real data.
- `paper/` contains the Quarto document, the bibliography, the citation style, the figures and the rendered PDF.
- `other/sketches/` contains sketches of the planned dataset and figures.
- `other/literature/` contains City of Toronto and Public Health Ontario documents on how the data are collected.
- `other/results/` contains the tables of results written by `scripts/07-analyse_data.py`.
- `other/explore/` contains notebooks used to explore the raw data and explain the model.
- `other/llm_usage/` contains the complete chats with LLMs (see below).

## Reproducing the paper

The project uses [uv](https://docs.astral.sh/uv/) with Python 3.14. Rendering the paper also needs [Quarto](https://quarto.org/) and a LaTeX installation. From the project root:

```bash
uv sync                                           # install the packages in uv.lock
uv run scripts/00-simulate_data.py                # simulate data (seeded)
uv run scripts/01-test_simulated_data.py          # test the simulated data
uv run scripts/02-download_data.py                # download the raw data
uv run scripts/03-clean_data.py                   # clean the raw data
uv run scripts/04-test_analysis_data.py           # test the cleaned data
uv run scripts/05-exploratory_data_analysis.py    # draw the data figures
uv run scripts/06-validate_on_simulated_data.py   # check the analysis on simulated data
uv run scripts/07-analyse_data.py                 # analyse the real data
cd paper && uv run quarto render paper.qmd        # render paper/paper.pdf
```

The paper reads only the saved files in `data/`, `other/results/` and `paper/figures/`, so it can be rendered without running the scripts. Running `02-download_data.py` again replaces the saved raw data with the current version on Open Data Toronto, which may differ from the 22 September 2026 download used in the paper. The map in `05-exploratory_data_analysis.py` downloads basemap tiles, so that script needs an internet connection.

Code is formatted and linted with ruff (`uv run ruff format .` and `uv run ruff check .`).

## Statement on LLM usage

Claude (Anthropic) was used throughout this project, and every chat is included in full in `other/llm_usage/`:

- `00-claude-browser-chat.txt` is a chat with Claude in the browser (claude.ai), used to choose a dataset, set up the repo, understand how the City measures *E. coli* and posts warnings, plan the simulation and analysis, and discuss the preliminary results and the writing.
- `01-` to `05-` are sessions with Claude Code, which wrote most of the code (the scripts, tests and analysis functions) and drafted and revised the paper with the author, who directed the work and checked and edited the results and the text.

No autocomplete tool was used.
