# Workflow Engine

A distributed workflow orchestration engine for reliable execution of long-running processes.

**Correctness comes from durable state transitions, not process-local memory.**

Built with FastAPI, PostgreSQL, and stateless background workers, this system focuses on durable execution, concurrency safety, and failure-aware workflow progression using the database as the source of truth.

---

## Key Highlights

- Database-driven execution (no in-memory queue dependency)
- Atomic step claiming for safe multi-worker execution
- Idempotent step execution with retry + backoff
- Crash recovery via persisted workflow state
- Horizontal worker scaling using shared database coordination

---

## System Architecture

Client / API User  
        |  
        v  
   FastAPI (Control Plane)  
        |  
        v  
 PostgreSQL (Durable State)  
        |  
        v  
   Worker Processes  
 (poll → claim → execute → retry)

The database acts as the single source of truth for workflow and step state.  
Workers remain stateless and coordinate exclusively through persisted state.

---

## Architecture Components

| Component       | Responsibility                              |
|----------------|----------------------------------------------|
| FastAPI        | Workflow control plane (APIs, state updates) |
| SQLAlchemy     | Persistence and relational modeling          |
| PostgreSQL     | Durable workflow and step state storage      |
| Workers        | Polling, claiming, execution, retries        |
| Docker Compose | Local distributed environment simulation     |

---

## Execution Model

1. Create workflow and ordered steps  
2. Start workflow → first step becomes runnable  
3. Workers poll database for runnable steps  
4. One worker atomically claims a step  
5. Step executes  
6. On success → next step activated  
7. On failure → retry or fail workflow  

System correctness is derived from persisted state transitions rather than process-local memory.

---

## Core Design

### Durable State Machine

Workflow lifecycle:

CREATED → RUNNING → COMPLETED | FAILED  

Step lifecycle:

CREATED → RUNNING → COMPLETED | FAILED  

All state transitions are persisted in PostgreSQL, enabling reliable crash recovery and consistent workflow progression.

---

### Concurrency-Safe Execution

- Atomic step claiming implemented via conditional database updates  
- Guarantees single-worker execution for each step  
- Prevents duplicate processing in multi-worker environments  
- Verified using multi-worker race-condition testing  

---

### Idempotent Execution

- Safe retries for external side effects  
- HTTP steps use `Idempotency-Key`  
- Prevents duplicate execution effects after retries or failures  

---

### Retry & Failure Handling

Each step persists retry metadata:

- retry_count  
- max_retries  
- next_retry_at  

Retry strategy:

- Exponential backoff (capped)  
- Differentiates retriable vs terminal failures  
- Prevents tight retry loops  

---

### Crash Recovery

- Workers are stateless  
- Execution state stored in PostgreSQL  
- New workers resume execution from last persisted state  
- No in-memory dependency for workflow correctness  

---

## Failure Scenarios

Worker crash during execution  
→ Step state remains persisted in database  
→ Worker restart resumes execution safely  

Duplicate worker polling  
→ Atomic step claiming ensures only one worker executes the step  

Network failure during HTTP call  
→ Step marked failed and retried using exponential backoff  

Database restart  
→ Workers reconnect and resume processing using persisted state  

---

## Design Tradeoffs

Database coordination vs message queue  
→ Chose database coordination to prioritize durability and system simplicity  

Polling vs event-driven workers  
→ Polling provides predictable recovery behavior after worker crashes  

Sequential workflows vs DAG execution  
→ Initial implementation focuses on correctness and reliability before complexity  

Stateless workers vs in-memory state  
→ Stateless design enables horizontal scaling and crash resilience  

---

## Supported Step Types

- SLEEP  
- HTTP (with idempotency protection)

---

## Quick Start

cp .env.example .env  
docker compose up --build  

Verify:

curl http://localhost:8000/  

Expected response:

{"status":"ok"}

Services:

- API → localhost:8000  
- Postgres → 5432  
- Workers → configurable replicas  

---

## What This Project Demonstrates

- Workflow / job orchestration design  
- Distributed worker coordination  
- Concurrency control and race-condition handling  
- Durable execution using database as source of truth  
- Retry, idempotency, and failure-aware system behavior  
- Horizontal scaling with stateless workers  

---

## Roadmap

- DAG / branching workflows  
- Observability (metrics and tracing)  
- LLM / agentic workflow execution  
- Jittered retry strategies  
- Event-driven worker model  

---

## Summary

This is not just a task runner.

It is a backend execution engine that models real-world distributed system concerns:

- Durable state  
- Safe concurrency  
- Failure recovery  
- Reliable workflow execution  
- Predictable system behavior under failure