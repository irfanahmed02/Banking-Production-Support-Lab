# Banking Production Support Lab

A personal project simulating a banking payment transaction environment,
built to strengthen application-support and API skills alongside my
real-world payment operations background.

I work in a banking-sector NOC / IT Operations environment in Bahrain,
mostly monitoring and supporting payment applications rather than
building them. This project is my way of connecting what I actually know
about payment operations — transaction flows, EOD, incident
investigation — with hands-on Python, SQL, and API work, so I can
demonstrate the technical side of that knowledge, not just describe it.

**What this is:** a personal lab project demonstrating practical
application of Python, PostgreSQL, SQL, REST API design/testing,
transaction monitoring, incident simulation, and production-support
investigation.

## What it does

Simulates a small payment processing environment — transactions with
masked PANs, STAN/RRN, merchants, terminals, and response codes — then
lets me investigate it the way I'd investigate a real one: SQL analysis,
a controlled incident with a full RCA, a REST API to query and create
transactions, and application logging I can actually dig through with
grep.

## Stack

- **Python** — transaction generation, database access (psycopg2)
- **PostgreSQL** — transaction storage
- **FastAPI** — REST API layer
- **Postman** — API testing (full collection included)
- **Python `logging`** — application logging
- **Linux command-line tools** (grep, etc.) — log investigation

## Project structure

```
api/            FastAPI app (main.py) — all endpoints, logging, validation handling
database/       DB connection + query helpers (database.py), single-transaction script
scripts/        Batch transaction generator, controlled incident generator
docs/           RCA, log investigation notes, Postman collection
constant.py     Shared reference data (PANs, merchants, terminals, response codes)
logs/           Application log output (not committed — generated locally)
```

## What's built so far

- **Transaction data**: ~1,000+ generated transactions plus a controlled
  incident batch, with realistic masked PANs, STAN/RRN, merchants,
  terminals, and response codes (Approved, Declined, Insufficient Funds,
  Expired Card, Issuer Unavailable, System Error)
- **SQL investigation**: failure-rate analysis by merchant and terminal,
  distinguishing business declines from technical failures
- **A controlled incident + full RCA**: a run of System_Error
  transactions on one terminal, investigated and written up —
  [`docs/T004_INCIDENT_RCA.md`](docs/T004_INCIDENT_RCA.md)
- **A REST API** (FastAPI): health check with real DB-dependency checking,
  transaction lookup by ID and RRN, all transactions for a terminal, and
  creating a new transaction — with input validation and correct HTTP
  status codes throughout
- **A full Postman test suite** covering success and failure cases for
  every endpoint (not-found, invalid input, missing fields), included in
  [`docs/Banking Production Support Lab API.postman_collection.json`](docs/Banking Production Support Lab API.postman_collection.json) as an exportable collection
- **Application logging**, with severity levels chosen to actually mean
  something — a technical failure logs differently from a normal decline
  or a malformed request — and a log-investigation writeup using grep to
  find and reason about what's in there:
  [`docs/LOG_INVESTIGATION.md`](docs/LOG_INVESTIGATION.md)

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | API + database health check |
| GET | `/transactions/{id}` | Look up a transaction by ID |
| GET | `/transactions/rrn/{rrn}` | Look up a transaction by RRN |
| GET | `/terminals/{id}/transactions` | All transactions for a terminal |
| POST | `/transactions` | Create a new transaction |

## Running it locally

```
# clone and set up a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# set up PostgreSQL and update credentials in database/database.py

# run the API
cd api
uvicorn main:app --reload
```

Swagger docs available at `http://127.0.0.1:8000/docs` once running.
The Postman collection in `docs/Banking Production Support Lab API.postman_collection.json` can be imported directly for testing.

## What's next

Still working on: monitoring dashboards (Grafana), alerting, a couple more
incident scenarios, basic reconciliation, and an EOD-style reporting
workflow. This is an active, ongoing project.