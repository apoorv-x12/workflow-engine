Workflow Engine

A distributed workflow orchestration engine designed for reliable execution of long-running processes.

---

Key Highlights

- Database-driven execution (no in-memory queue dependency)
- Multi-worker coordination with atomic step claiming
- Idempotent step execution with retry + backoff
- Crash recovery using persisted workflow state
- Designed as an execution layer for workflow / agent systems

---

Why this matters

Most background job systems work in simple cases but break under concurrency, retries, and failures.

This system focuses on:

- durable state transitions
- safe multi-worker execution
- failure-aware workflow progression

---

Architecture

Component| Responsibility
FastAPI| workflow control plane and APIs
SQLAlchemy| persistence layer
Postgres| shared source of truth
Workers| polling, claiming, execution
Docker Compose| local distributed setup

---

Execution Model

1. Workflow + steps are created
2. Workflow starts → first step becomes runnable
3. Workers poll for runnable steps
4. One worker atomically claims a step
5. Step executes
6. On success → next step activated
7. On failure → retry or fail workflow

---

Core Design Concepts

Durable State Machine

- Workflow: "CREATED → RUNNING → COMPLETED | FAILED"
- Step: "CREATED → RUNNING → COMPLETED | FAILED"

All transitions are persisted in the database.

---

Concurrency-Safe Execution

- Atomic step claiming via conditional updates
- Prevents double execution across workers
- Race-condition tested

---

Idempotent Execution

- Safe retries for external calls
- HTTP steps use "Idempotency-Key"
- Prevents duplicate side effects

---

Retry & Failure Handling

- Per-step metadata: "retry_count", "max_retries", "next_retry_at"
- Exponential backoff (capped)
- Handles retriable vs terminal failures

---

Crash Recovery

- Workers are stateless
- Execution state stored in DB
- New workers resume from last state

---

Supported Step Types

- "SLEEP"
- "HTTP" (with idempotency protection)

---

Quick Start

cp .env.example .env
docker compose up --build

Verify:

curl http://localhost:8000/
# {"status":"ok"}

---

What this project demonstrates

- workflow / job orchestration design
- distributed worker coordination
- concurrency control and race handling
- durable execution using database as source of truth
- retry, idempotency, and failure-aware systems

---

Future Direction

This system can be extended into a full agent execution engine by adding:

- LLM-based planning layer
- dynamic workflow generation
- tool execution pipelines

---

Summary

This is not just a task runner.

It is a backend execution engine that models real-world concerns:
durable state, safe concurrency, retries, and failure-aware workflow execution.