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
DEFAULT_REGION=USA
```

## Run Backend Pipeline

```bash
python -m src.pipeline.build_dataset --region "USA" --hours 24 --output data/outages_latest.csv
```

## Official Feed Adapter and Replay Consumer

The backend now supports a strict timestamp-ordered replay consumer for the official feed requirement.

Configuration via environment variables:

- `OFFICIAL_FEED_SOURCE`: `csv` (default) or `api`
- `OFFICIAL_FEED_CSV_PATH`: local dataset path (default `data/outages_latest.csv`)
- `OFFICIAL_FEED_REPLAY_URL`: required when `OFFICIAL_FEED_SOURCE=api`
- `OFFICIAL_FEED_CURSOR_PATH`: persisted watermark cursor path (default `backend/.replay_cursor.json`)

Replay endpoints:

- `GET /feed/replay/status`: current cursor and pending docs
- `POST /feed/replay/next` with `{ "batch_size": N }`: consume next N docs in timestamp order and run NLP -> risk -> alert
- `POST /feed/replay/reset`: reset cursor to replay from the start

Example:

```bash
curl http://localhost:8000/feed/replay/status
curl -X POST http://localhost:8000/feed/replay/next -H "Content-Type: application/json" -d '{"batch_size": 3}'
curl -X POST http://localhost:8000/feed/replay/reset
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
