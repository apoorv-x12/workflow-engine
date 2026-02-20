# Workflow Engine (WIP)

A **production-oriented workflow orchestration backend**, focused on correctness, state transitions, and data modeling rather than UI or integrations.

This project intentionally models the **core backend problems** that show up in real systems:  
state machines, parent–child relationships, transactional updates, and evolvable design.

---

## Why this project exists

Most backend-heavy systems eventually become **workflow-driven**:

- payment processing
- document pipelines
- background jobs
- approval flows
- retries & failure recovery

Instead of building a “feature-heavy demo app”, this project focuses on the **fundamentals**:
> how workflows are modeled, transitioned, and kept consistent over time.

---

## What this project demonstrates

- Clear **entity lifecycle modeling**
- Explicit **state transitions** (command-style APIs)
- Relational modeling with **strong ownership guarantees**
- Backend-first thinking (correctness > UI)
- Incremental, evolvable system design

---

## Current Features

- **Workflow lifecycle**
  - `CREATED → RUNNING → COMPLETED / FAILED`
- **Workflow steps**
  - Parent–child modeling using foreign keys
  - Step-level state tracking
- **REST APIs**
  - Explicit command endpoints for state transitions
- **ORM-based persistence**
  - SQLAlchemy with relational integrity enforced at DB level

---

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** SQLite (development)
- **Planned:** PostgreSQL + migrations

---

## Design Decisions

### 1. Explicit state transitions over generic updates
Instead of a generic “update workflow” endpoint, state changes are modeled as **commands**  
(e.g. `start`, `complete`, `fail`).

**Why:**  
This mirrors real production systems where transitions are intentional, validated, and auditable.

---

### 2. Database-enforced ownership
Child entities (workflow steps) **cannot exist without a parent workflow**.

**Why:**  
This prevents invalid states and eliminates an entire class of production bugs.

---

### 3. Minimal schema first, behavior later
The schema focuses only on:
- identity
- ownership
- lifecycle state

Execution order, retries, and orchestration logic are deliberately deferred.

**Why:**  
Premature modeling of behavior slows development and hides core correctness issues.

---

### 4. ORM relationships as convenience, not dependency
`relationship()` is used for Python-level navigation, while **Foreign Keys remain the source of truth**.

**Why:**  
This keeps the data model correct even outside the ORM context.

---

### 5. Incremental production realism
The project evolves in phases:
1. Correct modeling
2. Safe state transitions
3. Execution & background processing
4. Observability & idempotency

**Why:**  
This reflects how real systems are built and maintained.

---

## In Progress / Planned Work

- Workflow step execution semantics
- Background execution model
- Idempotency handling
- PostgreSQL + migrations
- Observability (logging, metrics)
- Failure handling & retries

---

## Status

🚧 **Work in progress** — intentionally evolving toward a production-grade backend system.

This repository is meant to show **how I think about backend systems**, not just finished features.

---

## How to run locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload