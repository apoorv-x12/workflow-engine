# Workflow Engine

A production-minded workflow orchestration backend built with FastAPI, SQLAlchemy, Postgres, and background workers.

This project is designed to show backend engineering depth beyond CRUD APIs. It focuses on workflow state management, multi-worker coordination, failure handling, and durable execution using the database as the source of truth.

## Quick start

The fastest way to run the full system is with Docker Compose.

1. Copy `.env.example` to `.env`.
2. Start the stack:

```bash
docker compose up --build
```

3. Verify the API is up:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"status":"ok"}
```

This starts:

- Postgres on `5432`
- API on `8000`
- worker container(s) based on `WORKER_REPLICAS`

## Why this is a strong backend project

This codebase demonstrates practical distributed-systems thinking:

- explicit workflow and step state machines
- database-coordinated workers instead of in-memory job queues
- atomic step claiming to avoid double execution
- crash recovery using claim timeouts
- sequential workflow progression driven by durable state transitions
- retry scheduling with persisted backoff metadata
- containerized local environment with API, workers, and Postgres

Instead of optimizing for UI, this project focuses on the execution layer problems that real systems run into:

- job orchestration
- long-running background work
- concurrency safety
- failure recovery
- idempotent external calls
- state consistency across processes

## What is implemented today

### Control plane

The API supports:

- creating workflows
- adding ordered steps to a workflow
- starting a workflow
- completing or failing individual steps
- completing or failing the overall workflow
- fetching workflow state and step progress

### Execution plane

Background workers:

- poll for runnable steps
- only pick steps in `RUNNING` state
- respect `next_retry_at` before retrying failed executions
- use a conditional `UPDATE` plus `rowcount` check for atomic claiming
- execute step logic outside the API process
- call back into the API to transition state after execution

### Supported step executors

Current step types:

- `SLEEP`
- `HTTP`

For HTTP execution, the worker attaches an `Idempotency-Key` derived from workflow and step IDs so repeated attempts are safer against duplicate side effects.

### Retry behavior

Retry metadata is stored per step:

- `retry_count`
- `max_retries`
- `next_retry_at`

When step execution raises a retriable error, the worker schedules the next attempt using exponential backoff capped at 30 seconds.

### Data-model safety

The schema enforces useful invariants:

- unique step ordering per workflow
- unique step names per workflow
- foreign-key ownership from step to workflow

## Execution model

High-level flow:

1. API creates a workflow and its ordered steps.
2. Starting a workflow moves the workflow to `RUNNING` and activates the first step.
3. Workers poll the database for runnable steps.
4. A worker atomically claims one step.
5. The worker executes the step.
6. On success, the API marks the step complete and activates the next step.
7. On failure, the workflow is failed or the step is retried based on execution result.

This mirrors patterns used in orchestration systems, job runners, and workflow engines where correctness comes from durable state transitions, not from a single long-running process holding everything in memory.

## Lifecycle model

### Workflow lifecycle

`CREATED -> RUNNING -> COMPLETED | FAILED`

### Step lifecycle

`CREATED -> RUNNING -> COMPLETED | FAILED`

The design keeps transitions explicit and API-driven instead of allowing arbitrary status mutation.

## Concurrency and failure handling

One of the most valuable parts of this project is the worker coordination model.

Workers do not coordinate with each other directly. They coordinate through shared database state.

Current safety mechanisms:

- atomic step claiming via conditional update
- stale-claim recovery using a configurable timeout
- persisted retry schedule via `next_retry_at`
- race-condition tests for multi-worker claiming

This means the project is not just "can run background tasks", but "can run background tasks with multiple workers without casually double-processing the same work."

## Architecture

| Component | Responsibility |
|----------|----------------|
| FastAPI | workflow control plane and transition APIs |
| SQLAlchemy | persistence and relational modeling |
| Postgres | shared durable state across API and workers |
| Worker loop | polling, claiming, execution, retry scheduling |
| Docker Compose | local distributed environment |

## Local stack

The repository includes a containerized local setup with:

- Postgres
- FastAPI API service
- worker service
- configurable worker replica count

That makes it easy to demonstrate horizontal workers against a shared database, which is a much stronger hiring signal than a single-process demo.

## Tests

Current tests focus on worker claim races:

- threaded worker-claim race test
- multi-process worker-claim race test

These are especially useful because they validate one of the most important properties in the system: only one worker should successfully claim a runnable step.

## Tech stack

- Python
- FastAPI
- SQLAlchemy
- Postgres
- Requests
- Docker Compose

## Run locally

### Option 1: Docker Compose

1. Copy `.env.example` to `.env`.
2. Start the stack:

```bash
docker compose up --build
```

This starts:

- Postgres on `5432`
- API on `8000`
- worker container(s) based on `WORKER_REPLICAS`

### Option 2: Run API locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Example API flow

1. Create a workflow.
2. Add one or more ordered steps.
3. Start the workflow.
4. Let workers claim and execute the active step.
5. Inspect workflow status via the read endpoints.

## What this project signals to hiring teams

This project is a concrete signal for roles involving backend platforms, workflow systems, job processing, or distributed application design.

It shows experience with:

- modeling finite state transitions
- designing worker-based execution systems
- reasoning about concurrency and race conditions
- building around durable persistence instead of process-local state
- thinking about retries, timeouts, and idempotency
- shipping containerized services that work together

## Roadmap

The system is already useful as a backend architecture project, and there is a clear path to production-hardening:

- stronger retry semantics and jittered backoff
- richer workflow definitions and branching
- audit logs and observability
- Alembic migrations
- better terminal-state handling around worker callback failures
- more end-to-end and failure-path tests

## Summary

This is not just a task runner. It is a small workflow engine that models the real backend concerns behind orchestration systems: durable state, worker coordination, safe transitions, and failure-aware execution.
