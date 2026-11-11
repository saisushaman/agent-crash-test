# INTENT

> This document is the source of truth for scope. Any change to it is a human decision.

Status: approved input contract, 2026-11-11. Implementation not yet approved.

## Problem

An AI agent proposes a change to a service. Nobody can cheaply answer the question that matters before it lands: **what breaks if we do this, and is that acceptable?**

Existing coding assistants answer with an opinion. An opinion is not something a human can responsibly approve a deployment against.

## Product

Agent Crash Test takes a proposed API change, determines whether it breaks the published contract, verifies the change against the project's test suite in an isolated container, and produces a risk report that a human must approve before the change is applied.

## The MVP, precisely

Given **two OpenAPI specifications** — `original.yaml` and `proposed.yaml` — determine whether the proposed specification breaks the contract published by the original, and produce an approval-gated risk report.

Input contract (approved 2026-11-11):

- `original.yaml` — the existing OpenAPI specification
- `proposed.yaml` — the proposed OpenAPI specification
- OpenAPI **3.0 and 3.1** are both supported
- **YAML and JSON** are both accepted

## Core principle

**The verdict is deterministic. No language model sits in the verdict path.**

Breaking-change detection is static analysis: parse both contracts, diff them, classify each difference against a published rule set. The same input yields the same verdict on every run, and every finding traces to a named rule.

A language model may write the human-readable narrative and propose a safer alternative. Both are optional, both are non-blocking, and neither may alter the verdict. If the model is unavailable, the report still renders with its findings intact.

## Explicitly out of scope for the MVP

Named here so that later work cannot absorb them silently:

- **Git diffs** — the input is two specifications, not a patch
- **GitHub pull requests** — no VCS or forge integration
- **Runtime API introspection** — the original contract comes from a file, never from a live service
- **Database migrations** — no schema change analysis
- **Infrastructure analysis** — no Terraform, Kubernetes, or deployment config
- Non-HTTP interfaces (gRPC, GraphQL, message queues)
- Non-Python services (the sandbox runs pytest)
- Outbound actions of any kind (email, webhooks, notifications)
- File deletion or filesystem mutation analysis

## Operating rules

1. This document is the source of truth; scope changes are human decisions, never an agent's.
2. No implementation task begins without written acceptance criteria.
3. No task is complete without test evidence.
4. The deterministic core may never depend on a model being available.
5. Ambiguity is recorded as an open question, never resolved by invention.
