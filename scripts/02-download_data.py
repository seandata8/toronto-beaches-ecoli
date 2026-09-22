#### Preamble ####
# Purpose: Downloads and saves the Toronto Beaches Water Quality data from
# Open Data Toronto.
# Author: Sean Murphy
# Date: 22 September 2026
# Contact: seandata8@gmail.com
# License: MIT
# Pre-requisites:
# - `polars` must be installed (uv add polars)
# - Run from the project root: uv run scripts/02-download_data.py


#### Workspace setup ####
import json
from pathlib import Path
from urllib.request import urlopen

import polars as pl

CKAN_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_ID = "toronto-beaches-water-quality"
OUTPUT_PATH = Path("data/01-raw_data/raw_data.csv")

#### Download data ####
# Look up the package's resources through the Open Data Toronto (CKAN) API
with urlopen(f"{CKAN_BASE}/api/3/action/package_show?id={PACKAGE_ID}") as response:
    package = json.load(response)["result"]

# Keep the first CSV resource (WGS84 / EPSG:4326 coordinates)
csv_resource = next(
    resource for resource in package["resources"] if resource["format"] == "CSV"
)

# Scan every row before choosing column types, since eColi is blank in many rows
raw_data = pl.read_csv(csv_resource["url"], infer_schema_length=None)


#### Save data ####
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
raw_data.write_csv(OUTPUT_PATH)
print(f"Saved {raw_data.height} rows from '{csv_resource['name']}' to {OUTPUT_PATH}")

print(raw_data.head())
