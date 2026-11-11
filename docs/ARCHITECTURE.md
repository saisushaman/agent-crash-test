# ARCHITECTURE

Derived from [INTENT.md](INTENT.md). The governing constraint is that **the verdict is deterministic and no model sits in its path.**

## Pipeline

```
original.yaml ─┐
               ├─> Intake ──> Inventory ─┐
proposed.yaml ─┘                         │
                                         v
                              Contract differ ──> list[Change]
                                         │
                                         v
                              Sandbox runner (M2) ──> TestResults
                                         │
                                         v
                                  Risk scorer ──> score + band
                                         │
                                         v
                                   RiskReport ──> human approval (M4)

        optional, non-blocking, may not alter the verdict:
          LLM narrative ─┐
          LLM alternative ┴─> prose fields on RiskReport
```

Four deterministic stages produce the verdict. Two optional model-backed stages decorate it. Delete both model stages and the verdict is unchanged — that property is the architecture.

## Stage responsibilities

### 1. Intake

Reads both files, detects format by content, parses, validates, and normalises to `Inventory`. This is the **only** stage that knows about OpenAPI versions, YAML versus JSON, or `$ref` resolution. Every downstream stage sees one representation.

Isolating version handling here is what keeps the differ testable: the differ consumes `Inventory` objects and never parses a document.

**`$ref` resolution has three outcomes**, and Intake is where they are decided:

- **Local reference** → inlined. No `$ref` survives into `Inventory`.
- **Recognised cycle** → detected on the resolution stack, truncated at the cycle point, marked `recursive` with its origin pointer. Supported and expected; identical cycles compare equal, so recursion never registers as a change.
- **Depth exceeded without a cycle** → marked `depth_exceeded` and recorded as an `IndeterminateRegion`. The tool stopped looking and says so.

The difference between the second and third outcome is the difference between *elided deliberately* and *not examined*. A recognised cycle permits a definitive verdict; a depth-exceeded node does not. Collapsing the two would let the tool report "no breaking changes" about a subtree it never read — the most damaging failure available to it.

External references raise `UnsupportedSpecError` and are never fetched, because fetching would put network access in the deterministic core.

### 2. Contract differ

A pure function, `classify(before: Inventory, after: Inventory) -> list[Change]`.

No I/O, no network, no model. Given two inventories it emits an ordered list of typed, severity-classified changes, each carrying a rationale traceable to a named rule. This is the component the product's value rests on.

### 3. Sandbox runner — M2

Copies the target repository into a hardened container, selects tests relevant to the changed endpoints, runs pytest, and captures JUnit XML and the exit code.

Hardening is not optional, because the sandbox may execute code proposed by an agent: `--network=none`, read-only root with a writable `tmpfs`, all capabilities dropped, `no-new-privileges`, non-root user, explicit CPU, memory and PID limits, and a hard wall-clock timeout. The repository is copied in; the host filesystem is never bind-mounted.

This configuration is adequate for trusted-but-careless input. **It is not proof against a determined adversary.** Hardening beyond it means gVisor or Firecracker, and that limitation is documented rather than assumed away.

### 4. Risk scorer

Maps classified changes plus test results to a numeric score and a band, by published rules. Any single `breaking` change forces a band of at least `high`.

### 5. Optional model stages

Two, both off the critical path:

- **Narrative** — renders findings as readable prose
- **Safer alternative** — proposes a less damaging change

Both receive **structured findings only, never raw specification content**. This is a security property, not a style choice: specification `description` fields are attacker-controlled text, and feeding them to a model as instructions is a prompt-injection channel. Both degrade to template text on failure.

## Why no LangGraph

The pipeline runs the same stages in the same order every time. That is a function call graph, not an agent loop.

Plain Python costs less, runs faster, and is reproducible — the same input yields the same verdict, which is what makes a report auditable. A graph framework introduced to express a straight line adds a dependency and a failure mode while buying nothing.

If genuine multi-agent control flow appears later — negotiation between competing fixes, iterative repair loops — revisit the decision then, on evidence.

## Why SQLite first

SQLAlchemy models from day one; SQLite as the engine until M4. The schema stays Postgres-compatible so the migration is a connection-string change.

This honours the rule against unnecessary infrastructure and avoids standing up Postgres before Docker exists on the host.

## Module layout

```
src/agent_crash_test/
  intake/        parse, validate, normalise      (FR-1)
  models/        Inventory, Change, RiskReport   (DATA_MODELS.md)
  differ/        classify(), rule set            (FR-2)
  sandbox/       container runner        M2      (FR-5, NFR-3)
  scoring/       score(), bands                  (FR-3)
  report/        assembler, serialisation        (FR-4)
  narrative/     optional model stages           (NFR-4)
  api/           FastAPI app             M4      (FR-4)
  persistence/   SQLAlchemy models       M4
```

Dependency direction is strictly downward: `differ` imports `models`, never `intake`. Nothing imports `narrative`.

## Error handling strategy

Errors are typed, specific, and loud. The failure mode to design against is a silent empty result, because an empty change list reads as "safe."

| Condition | Error | Carries |
| --- | --- | --- |
| Malformed YAML or JSON | `SpecParseError` | file, line or offset |
| Not an OpenAPI document | `SpecFormatError` | file, what was found |
| Swagger 2.0 / 4.x / external `$ref` | `UnsupportedSpecError` | file, found, supported |
| Violates OpenAPI schema | `SpecValidationError` | file, list of JSON pointers |
| Zero paths | `EmptySpecError` | file |

All derive from `AgentCrashTestError`. No error path returns a partial or empty `RiskReport`. A 3.0-versus-3.1 comparison is permitted, and differences attributable solely to the version are classified `informational`.
