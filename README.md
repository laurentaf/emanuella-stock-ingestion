# Emanuella Stock Ingestion Pipeline

Weekly inventory forecast ingestion pipeline for **Lojas Emanuella**.

3-stage ETL pipeline that consumes data from the DataMission API, transforms it,
and generates dbt-ready artifacts.

---

## EN Quick Summary

**Stack:** Python 3.10+ · pandas · requests · dbt (staging model)

**What it does:** Ingestion pipeline that fetches weekly inventory data from the
DataMission API, transforms it to a clean staging CSV, and generates a commented
dbt staging model ready to drop into a dbt project.

**Proves:** API ingestion, pandas transformation, dbt-ready data modeling,
CI/CD scheduling (GitHub Actions).

**Run:** `python scripts/ingestion.py`

---

## Architecture

```
API DataMission
      │
      ▼
┌─────────────────┐
│ Stage 1         │  fetch_inventory_data()
│ Ingestion via API│  → data/inventory_staging.json (raw JSON)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Stage 2         │  transform_inventory()
│ Transformation  │  Reads JSON from disk, selects key columns
│                 │  → data/inventory_staging.csv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Stage 3         │  generate_metadata()
│ dbt Artifacts   │  → data/inventory_metadata.json
│                 │  → sql/staging_inventory.sql
└─────────────────┘
```

## Prerequisites

- Python 3.10+
- pip

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/laurentaf/emanuella-stock-ingestion.git
cd emanuella-stock-ingestion

# 2. Create virtual environment
python -m venv .venv

# 3. Activate the environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

## API Configuration

The script requires a DataMission API token. Configure it in one of these ways:

### Option 1: .env file (recommended)

```bash
# Copy the example file and add your token
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac
```

Edit `.env` and replace `your-token-here` with your DataMission token.

### Option 2: Environment variable

```bash
# Windows PowerShell:
$env:API_TOKEN = "your-token-here"

# Linux/Mac:
export API_TOKEN="your-token-here"
```

## Run

```bash
python scripts/ingestion.py
```

The pipeline executes all 3 stages in sequence and produces:

| Stage | Output File | Description |
|-------|-------------|-------------|
| 1 | `data/inventory_staging.json` | Raw JSON with all API records |
| 2 | `data/inventory_staging.csv` | Transformed CSV with selected columns |
| 3 | `data/inventory_metadata.json` | Simple schema (column/name/type) |
| 3 | `sql/staging_inventory.sql` | Commented dbt staging model |

## Data

The API returns 1,000 records with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | string | Unique order identifier (UUID) |
| `timestamp` | datetime | ISO date/time of the order |
| `customer_id` | integer | Customer identifier |
| `product_category` | string | Product category |
| `price` | float | Unit price in BRL |
| `quantity` | integer | Number of units |
| `store_location` | string | Store name |

## Quality Rules

See [data/quality_rules.md](data/quality_rules.md) for the documented
quality rules applied to the data.

## Schedule (Trigger / SLA)

The pipeline runs manually or can be scheduled via cron/CI.
See [.github/workflows/ingest.yml](.github/workflows/ingest.yml).

**Suggested trigger:** daily at 06:00 UTC
**Suggested SLA:** full pipeline in < 5 minutes (for 1,000 records)

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Records ingested per run | 1,000 (API cap) |
| Staging output | `data/inventory_staging.csv` |
| dbt staging model | `sql/staging_inventory.sql` (commented, ready to use) |
| Data quality rules | 4 rules documented in `data/quality_rules.md` |
| Schedule | Daily at 06:00 UTC via GitHub Actions |

---

## 💼 What This Proves

| Skill | Evidence |
|-------|----------|
| API ingestion | `requests` with Bearer token, JSON → DataFrame |
| Data modeling | Generates `staging_inventory.sql` — commented dbt model |
| ETL pipeline | 3-stage: fetch → transform → artifact generation |
| Data quality | 4 DQ rules checked, documented in `data/quality_rules.md` |
| CI/CD | `.github/workflows/ingest.yml` — daily trigger, SLA < 5 min |
| Downstream readiness | Outputs a clean CSV + dbt SQL ready for transformation |

---

## Connect to dbt

The generated `sql/staging_inventory.sql` is a drop-in dbt staging model:

```sql
-- sql/staging_inventory.sql
with source as (
    select * from {{ ref('inventory_staging_csv') }}
),
renamed as (
    select
        order_id,
        customer_id,
        -- ...
        store_location
    from source
)
select * from renamed
```

Then in your dbt project:
```bash
cp sql/staging_inventory.sql your-dbt-project/models/staging/
dbt run --select staging_inventory
```

---

*Built with [LAOS](https://github.com/laurentaf/laos) — Laurent Agent Operating System.*