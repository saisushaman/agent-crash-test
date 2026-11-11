# MILESTONES

Six milestones. Each has a gate that must be **demonstrated** before the next begins. No milestone completes on "code written" — only on evidence produced.

## M0 — Data contracts

Project setup, then the six frozen data contracts — `Inventory`, `Endpoint`, `Parameter`, `SchemaProperty`, `Change`, `RiskReport` — plus `IndeterminateRegion` and the exception hierarchy. The contracts come first because every later stage writes to them, and because a corpus or classifier built against an unsettled shape has to be rebuilt.

Also in M0: ordering guarantees enforced at construction, canonical JSON serialisation, JSON round-trip tests, and **three representative fixture pairs** (one clearly breaking, one clearly compatible, one identical). A contract you cannot express a fixture against is not finished.

**Gate:**

- Six models frozen, with ordering applied at construction rather than serialisation
- The 14 change types defined as a closed enum, severity rules present as reviewable data
- `RiskReport` round-trips to JSON and back
- Canonical serialisation verified: same object, 10 serialisations, byte-identical
- Three representative fixture pairs exist and are expressible in `Change` records
- CI green on lint, type check and pytest

**Not in M0:** any OpenAPI parsing, any comparison logic, any scoring.

## M1 — Parsing and classification

Intake (parse, validate, resolve `$ref`, normalise 3.0 and 3.1, YAML and JSON) and the deterministic classifier over the 14 change types. The fixture corpus expands from three pairs to the full 27.

**Gate:**

- All fixtures in [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) classify correctly, covering all 14 types and all 5 error conditions
- A 3.0 document and its 3.1 equivalent produce equivalent inventories
- The same API in YAML and in JSON produces identical inventories
- Recursive schemas resolve without error, and identical cycles register zero changes
- A schema exceeding depth 8 without a cycle yields `band: indeterminate`, never a compatible verdict
- Determinism verified over 10 runs

**Not blocked by Docker.** M0 and M1 together are the highest-value work and have no infrastructure dependency.

## M2 — Sandbox

Container image for the Python test runner, the sandbox runner, the hardening profile, escape-attempt fixtures, and the test-selection heuristic.

**Gate:** a deliberately failing suite is reported correctly; every escape fixture fails closed; the hardening profile is asserted in tests, not just documented.

**Blocked on Docker**, which is not installed on the current host. If Docker slips, M1 proceeds without it and M2 moves after M3.

## M3 — Risk engine

Deterministic scorer, report assembler, determinism test. The two optional model stages are added last, behind a feature flag, and must degrade cleanly.

**Gate:** identical input produces byte-identical reports across 10 runs. With the model disabled, reports still render with `narrative_source: "template"`.

## M4 — Approval gate

FastAPI service, SQLAlchemy persistence, approve/reject workflow, immutable audit trail, authentication on the approval endpoint.

**Gate:** no change can be marked applied without a recorded human decision; the audit trail cannot be edited after the fact.

## M5 — Dashboard

React and TypeScript, with the client generated from FastAPI's OpenAPI output.

**Gate:** a reviewer reads a report and approves or rejects without touching the API directly.

## Dependencies

```
M0 --+--> M1 --+--> M3 --> M4 --> M5
     +--> M2 --+
```

M1 and M2 are independent of each other and may run in parallel once M0 lands. M3 requires both. M5 needs only M4's frozen API contract.

## Ownership

| Milestone | Primary | Reviewer |
| --- | --- | --- |
| M0 | CTO / Architect | CEO |
| M1 | Backend Engineer | CTO, QA owns the corpus |
| M2 | QA / Security Engineer | CTO |
| M3 | Backend Engineer | CTO |
| M4 | Backend Engineer | CTO, CEO on the approval semantics |
| M5 | Frontend Engineer | CTO |

The fixture corpus belongs to QA, not to the engineer writing the differ. A corpus written by the same person who wrote the classifier tests what was built, not what was specified.

## Open questions carried into implementation

These need human decisions. None may be resolved by an agent.

- [ ] **Is the analysed repository trusted?** Determines whether the M2 hardening profile suffices or gVisor is required before shipping.
- [ ] **Latency budget?** Inline feedback implies under two minutes; an overnight report allows a far more thorough run.
- [ ] **Does "safer alternative" mean prose or an applicable patch?** Generating a patch is a substantially larger project.
- [ ] **Docker installation timeline?** M2 is blocked until it exists on the host.
- [ ] **Which model backs agent-executed tasks?** Local qwen3:8b has been measured as insufficient for architectural work.
