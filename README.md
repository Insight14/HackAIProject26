# HackAIProject26

Full-stack outage-risk prototype for HackAI 2026.

- Frontend: React + Vite dashboard (`src/` JSX files)
- Backend ingestion: Python data pipeline (`src/` Python package)

## Backend Data Sources

- EIA grid operations data (demand / generation)
- DOE OE-417 disturbance summaries
- ORNL ODIN real-time outages (county-level)

The ingestion pipeline produces a unified CSV at `data/outages_latest.csv`.

## Backend Setup

1. Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Python deps:

```bash
pip install -r requirements.txt
```

3. Add `.env` in project root:

```env
EIA_API_KEY=your_eia_api_key_here
DEFAULT_REGION=Texas
```

## Run Backend Pipeline

```bash
python -m src.pipeline.build_dataset --region "Texas" --hours 24 --output data/outages_latest.csv
```

## Frontend Setup

Install Node dependencies:

```bash
npm install
```

Run dev server:

```bash
npm run dev
```

Build production bundle:

```bash
npm run build
```
