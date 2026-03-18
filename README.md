# Workflow Engine

A distributed workflow orchestration engine for reliable execution of long-running processes.

Built with FastAPI, Postgres, and background workers, this system focuses on **durable execution, concurrency safety, and failure-aware workflow progression** using the database as the source of truth.

---

## Key Highlights

- Database-driven execution (no in-memory queue dependency)
- Atomic step claiming for safe multi-worker execution
- Idempotent step execution with retries and backoff
- Crash recovery via persisted workflow state
- Horizontal worker scaling using shared database coordination

---

## Architecture

| Component       | Responsibility                              |
|----------------|----------------------------------------------|
| FastAPI        | workflow control plane (APIs, state updates) |
| SQLAlchemy     | persistence and relational modeling          |
| Postgres       | durable source of truth                      |
| Workers        | polling, claiming, execution, retries        |
| Docker Compose | local distributed environment                |

---

## Execution Model

1. Create workflow and ordered steps  
2. Start workflow → first step becomes runnable  
3. Workers poll database for runnable steps  
4. One worker atomically claims a step  
5. Step executes (HTTP / task logic)  
6. On success → next step activated  
7. On failure → retry or fail workflow  

Correctness comes from **durable state transitions**, not process-local memory.

---

## Core Design

### Durable State Machine

Workflow: `CREATED → RUNNING → COMPLETED | FAILED`  
Step: `CREATED → RUNNING → COMPLETED | FAILED`

All transitions are persisted and API-driven.

---

### Concurrency-Safe Execution

- Atomic step claiming via conditional `UPDATE`
- Only one worker can execute a step
- Verified with multi-worker race-condition tests

---

### Idempotent Execution

- Safe retries for external side effects
- HTTP steps use `Idempotency-Key`
- Prevents duplicate execution effects

---

### Retry & Failure Handling

Each step stores:

- `retry_count`
- `max_retries`
- `next_retry_at`

- Exponential backoff (capped)
- Distinguishes retriable vs terminal failures

---

### Crash Recovery

- Workers are stateless
- Execution state stored in Postgres
- New workers resume from last persisted state

---

## Supported Step Types

- `SLEEP`
- `HTTP` (with idempotency protection)

---

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Verify:

```bash
curl http://localhost:8000/
# {"status":"ok"}
```

Services:
- API → `localhost:8000`
- Postgres → `5432`
- Workers → configurable replicas

---

## What this project demonstrates

- workflow / job orchestration design
- distributed worker coordination
- concurrency control and race-condition handling
- durable execution using database as source of truth
- retry, idempotency, and failure-aware systems

---

## Roadmap

- branching workflows and DAG support
- improved retry strategies (jittered backoff)
- observability (logs, metrics, tracing)
- migration support (Alembic)
- deeper failure-path testing

---

## Summary

This is not just a task runner.

It is a backend execution engine that models real-world concerns:
durable state, safe concurrency, retries, and failure-aware workflow execution.