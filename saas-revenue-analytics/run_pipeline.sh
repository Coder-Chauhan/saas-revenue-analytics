#!/usr/bin/env bash
# End-to-end pipeline: generate sources -> extract/load -> dbt build (models + tests) -> monitor -> export.
set -euo pipefail
cd "$(dirname "$0")"
python scripts/generate_sources.py
python scripts/extract_load.py
dbt build --profiles-dir .
python scripts/monitor_data_quality.py
python scripts/export_for_powerbi.py
