# Trivial Todo App — Greenfield Specification (P6 C15)

Minimal greenfield spec for first working V1: add, list, mark done. Single wave; suitable for autonomous build.

## Project Overview

**Name**: Trivial Todo App  
**Description**: A minimal todo application with add, list, and mark-done only.  
**Goal**: Demonstrate Overlord greenfield path end-to-end (human at gates only).

## Objectives

- [ ] Add a todo (title)
- [ ] List all todos
- [ ] Mark a todo as done

## Key Requirements

### Functional Requirements

1. **Add todo**: User can add a todo with a title (string).
2. **List todos**: User can list all todos (title, done flag).
3. **Mark done**: User can mark a todo as done by identifier or index.

### Non-Functional

- Single wave of work (minimal scope).
- CLI or simple UI; check.sh runs and passes (lint/test).

## Out of Scope for Trivial

- Persistence (in-memory OK).
- Auth, real-time sync, mobile — not required for first working V1.
