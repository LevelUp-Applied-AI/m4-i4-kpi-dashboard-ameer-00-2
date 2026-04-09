[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/FBI2cyc1)
# Integration 4 — KPI Dashboard: Amman Digital Market

Design a KPI framework, compute metrics from the Amman Digital Market database, validate patterns with statistical tests, and produce an executive summary with supporting visualizations.

## Setup

1. Start PostgreSQL container:
   ```bash
   docker run -d --name postgres-m4-int \
     -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=amman_market \
     -p 5432:5432 -v pgdata_m4_int:/var/lib/postgresql/data \
     postgres:15-alpine
   ```
2. Load schema and data:
   ```bash
   psql -h localhost -U postgres -d amman_market -f schema.sql
   psql -h localhost -U postgres -d amman_market -f seed_data.sql
   ```
3. Install dependencies: `pip install -r requirements.txt`

## Deliverables

1. **`kpi_framework.md`** — Define 5 KPIs (at least 2 time-based, 1 cohort-based)
2. **`analysis.py`** — Extract data, compute KPIs, run statistical tests, create visualizations
3. **`EXECUTIVE_SUMMARY.md`** — Top findings, supporting data, recommendations
4. **`output/`** — Chart PNG files (at least 5, one per KPI)
5. **`tests/test_analysis.py`** — Your own tests (3 required)

## Challenge Extensions

### Tier 1: Interactive Dashboard with Plotly
- **File**: `analysis.py` (updated)
- **Output**: `output/dashboard.html` - Standalone interactive HTML dashboard
- **Features**: Hover tooltips, zoom, pan, responsive design
- **Run**: `python analysis.py`

### Tier 2: Automated KPI Monitoring Script
- **File**: `kpi_monitor.py`
- **Config**: `config.json` - Thresholds and filter options
- **Output**: `output/kpi_monitor_dashboard.html` - Monitoring dashboard with gauges
- **Features**: Green/yellow/red status indicators, dropdown filters, gauge visualizations
- **Run**: `python kpi_monitor.py`
- **Tests**: `tests/test_kpi_monitor.py`

### Tier 3: Multi-Page Analytical Report with Plotly Dash
- **File**: `app.py`
- **Features**: 
  - Page 1: KPI overview with gauge indicators
  - Page 2: Time-series deep dive with date range selector
  - Page 3: Cohort comparison with drill-down capability
  - Cross-filtering between pages
- **Run**: `python app.py` (starts on http://127.0.0.1:8050)

### Additional Dependencies
```bash
pip install plotly dash
```

---

## License

This repository is provided for educational use only. See [LICENSE](LICENSE) for terms.

You may clone and modify this repository for personal learning and practice, and reference code you wrote here in your professional portfolio. Redistribution outside this course is not permitted.
