# Workflow Engine (WIP)

A **production-oriented distributed workflow orchestration backend**, focused on correctness, execution safety, and state transitions rather than UI or integrations.

This project models the **core backend problems** that show up in real systems:

- state machines
- background execution
- concurrency safety
- failure recovery
- transactional consistency

Instead of building another CRUD-style service, this focuses on:

> how workflows are modeled, executed, and kept consistent under concurrency.

---

## Why this project exists

Most real backend systems eventually become workflow-driven:

- payment processing
- background jobs
- document pipelines
- AI / LLM pipelines
- approval systems
- automation engines

This project focuses on:

- lifecycle modeling  
- safe transitions  
- multi-worker execution  
- race-condition avoidance  

---

## What this project demonstrates

- Explicit state-machine design  
- Durable orchestration via DB state  
- Parent–child ownership modeling  
- Multi-worker safe execution  
- Optimistic locking for step claiming  
- Crash recovery via claim timeouts  
- Command-style transition APIs  

---

## Lifecycle

### Workflow
CREATED → RUNNING → COMPLETED / FAILED

### Step
CREATED → RUNNING → COMPLETED / FAILED

---

## Execution Model

Workers:

1. Poll DB for runnable steps  
2. Atomically claim via conditional UPDATE  
3. Execute work  
4. Complete step → next step auto-starts  

Execution flow:

DB State → Worker Poll → Atomic Claim → Execute → Transition

This mirrors real orchestration systems like:

- Temporal  
- Step Functions  
- CI/CD job runners  

---

## Concurrency Safety

Only one worker executes a step using:

conditional UPDATE + rowcount check

Crash recovery enabled via:

claimed_by < now - timeout

---

## Architecture

| Component | Role |
|----------|------|
| FastAPI | Control plane |
| SQLAlchemy | State persistence |
| SQLite | Durable execution state |
| Worker Loop | Execution plane |
| DB Constraints | Ownership guarantees |
| Optimistic Locking | Multi-worker safety |

Workers coordinate via the database — not with each other.

---

## Design Principles

- Explicit transitions over generic updates  
- Database as source of truth  
- Ownership enforced at schema level  
- Horizontal execution via workers  
- Incremental production realism  

---

## Tech Stack

- Python  
- FastAPI  
- SQLAlchemy 2.x  
- SQLite (dev)  
- Uvicorn  

Planned:

- PostgreSQL  
- Alembic migrations  
- Observability  
- Retries & backoff  

---

## Status

🚧 Work in progress — evolving toward a production-grade orchestration backend.

This project demonstrates how backend systems are designed to remain consistent under concurrency and failure.

---

## Run locally

pip install -r requirements.txt  
uvicorn app:app --reload
