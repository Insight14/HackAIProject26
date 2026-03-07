## Power Outage Risk – Data Ingestion (v1)

This branch (`v1poweroutage`) focuses on the **power outage prediction** part of the HackAI 2026 project.  
Goal for this slice: build a small Python backend module that **fetches and normalizes public outage-related data** so the rest of the system can compute risk scores and drive the dashboard.

### Scope of this branch

- **Data ingestion only (MVP)**:
  - EIA grid operations data (demand / generation / region)
  - DOE OE-417 disturbance / outage incident summaries
  - ORNL ODIN real-time outage data (county-level incidents)
- **Unified internal record** so everything looks like:

```json
{
  "region": "Texas",
  "timestamp": "2026-03-07T12:00:00Z",
  "demand_mw": 1200.0,
  "generation_mw": 1100.0,
  "weather_alert": "High Wind Warning",
  "disturbance_text": "Transmission failure due to storm"
}
```

Risk scoring, NLP, and UI will be layered on top in later branches.

### Project layout

- `src/`
  - `config.py` – shared configuration (e.g. API keys, regions)
  - `models.py` – pydantic models for unified records
  - `data_sources/`
    - `eia_client.py` – helpers for EIA Open Data API
    - `oe417_client.py` – helpers for DOE OE-417 annual summary data
    - `poweroutage_client.py` – ORNL ODIN outage API client
  - `pipeline/`
    - `build_dataset.py` – orchestration to pull from all sources and emit a unified dataframe or CSV

### Setup

1. **Create a virtualenv (recommended)**

```bash
python -m venv .venv
source .venv/bin/activate  # on macOS / Linux
# .venv\Scripts\activate   # on Windows
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the project root:

```bash
EIA_API_KEY=your_eia_api_key_here
DEFAULT_REGION=Texas
```

> NOTE: The EIA API key is required for EIA live calls. OE-417 and ODIN outage data are public endpoints.

### Running the ingestion pipeline (local)

For now, we expose a simple CLI entry point:

```bash
python -m src.pipeline.build_dataset --region "Texas" --hours 24 --output data/outages_latest.csv
```

This will:

- Fetch recent grid data from EIA (where possible)
- Fetch / refresh OE-417 incident summaries (if configured)
- Normalize into a single pandas DataFrame
- Save to the `data/` folder as a CSV for downstream modeling and UI.

### Next steps (future branches)

- Add **risk scoring** (grid stress score, low/medium/high).
- Add **NLP incident parsing** on top of disturbance text.
- Wrap this ingestion + scoring into HTTP endpoints (FastAPI / Flask).
- Plug into the **frontend dashboard** and alerting system.

