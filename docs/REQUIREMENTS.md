# REQUIREMENTS

Derived from [INTENT.md](INTENT.md). Requirements are numbered for traceability from acceptance criteria and tasks.

## Functional requirements

### FR-1 Specification intake

- **FR-1.1** Accept two specification files: `original` and `proposed`.
- **FR-1.2** Support OpenAPI **3.0.x** and **3.1.x**.
- **FR-1.3** Accept **YAML** and **JSON**, detected by content, not by file extension.
- **FR-1.4** Normalise both documents to a single internal `Inventory` representation, so that downstream stages never branch on spec version or file format.
- **FR-1.5** Resolve local `$ref` pointers within a document by inlining. No `$ref` survives into `Inventory`.
- **FR-1.6** Detect recursive schemas by tracking the resolution stack. A recognised cycle is truncated at the cycle point, marked `resolution: "recursive"` with its `cycle_origin`, and is **not** an error. Identical cycles in both documents compare equal, so recursion alone never registers as a change.
- **FR-1.7** Stop expansion at a configured depth limit (default **8**, identical for both documents). A node reaching the limit **without** a detected cycle is marked `resolution: "depth_exceeded"` and recorded as an `IndeterminateRegion`.
- **FR-1.8** External and remote `$ref` resolution is **out of scope** and must fail with a typed error (see FR-5.3). External references are never fetched: fetching would introduce network access into the deterministic core, violating NFR-3.1.

### FR-2 Contract comparison

- **FR-2.1** Compare two `Inventory` objects and emit an ordered list of `Change` records.
- **FR-2.2** Classify every change as one of the 14 types defined in [DATA_MODELS.md](DATA_MODELS.md).
- **FR-2.3** Assign each change a severity of `breaking`, `compatible`, or `informational` from the published rule set.
- **FR-2.4** Attach a non-empty `rationale` to every change, traceable to a named rule.
- **FR-2.5** Comparison is a pure function: no I/O, no network, no model calls.
- **FR-2.6** Output ordering is stable and defined (by path, then method, then change type).
- **FR-2.7** Apply the compatibility perspective: for a **request** parameter the breaking direction is the server accepting **fewer** inputs; for a **response** property it is the server potentially returning **more** kinds of output. Both reduce to: breaking when the other side must handle something it did not have to handle before.
- **FR-2.8** Direction must be proved against the ordering table or a subset test. An incomparable pair (`string`→`boolean`) is classified breaking with `comparability: "unproven"`, and its rationale states that compatibility could not be proven — it must never assert a narrowing or widening that was not demonstrated.

### FR-3 Risk scoring

- **FR-3.1** Compute a numeric risk score from the classified changes and, from M2, the test results.
- **FR-3.2** Map the score to a band: `none`, `low`, `medium`, `high`, `critical`, or `indeterminate` (see FR-6.2).
- **FR-3.3** Scoring is deterministic and rule-driven. No model participates.
- **FR-3.4** Any single `breaking` change forces a band of at least `high`.

### FR-4 Reporting and approval

- **FR-4.1** Emit a `RiskReport` conforming to the schema in [DATA_MODELS.md](DATA_MODELS.md).
- **FR-4.2** The report records every change, its severity, its rationale, and the score.
- **FR-4.3** From M4, no change may be marked applied without a recorded human decision.
- **FR-4.4** Decisions are immutable and auditable.

### FR-5 Error handling

Invalid input must fail loudly and specifically. A silent empty result is a defect, because an empty change list reads as "this change is safe."

- **FR-5.1 Unparseable file** — malformed YAML or JSON raises `SpecParseError` naming the file and the line or byte offset.
- **FR-5.2 Not an OpenAPI document** — a well-formed file missing a recognisable `openapi` version field raises `SpecFormatError`.
- **FR-5.3 Unsupported version** — Swagger 2.0, OpenAPI 4.x, or an unresolvable external `$ref` raises `UnsupportedSpecError` naming what was found and what is supported.
- **FR-5.4 Structurally invalid** — a document that parses but violates the OpenAPI schema raises `SpecValidationError` listing each offending JSON pointer.
- **FR-5.5 Incomplete specification** — a document with zero paths raises `EmptySpecError`. It is never treated as "no endpoints, therefore no changes."
- **FR-5.6 Version mismatch** — comparing a 3.0 original with a 3.1 proposal is **permitted**; both normalise to the same `Inventory`. Any change attributable solely to the version difference is classified `informational`.
- **FR-5.7** Every error names the offending file (`original` or `proposed`) so the user knows which to fix.
- **FR-5.8** No error path returns a partial or empty `RiskReport`.

### FR-6 Indeterminate results

- **FR-6.1** A `depth_exceeded` node must never yield a definitive compatibility verdict for the endpoint containing it.
- **FR-6.2** When `RiskReport.indeterminate` is non-empty, `band` is `indeterminate` regardless of score.
- **FR-6.3** No endpoint listed in `indeterminate` may carry a `compatible` conclusion.
- **FR-6.4** Report wording states *"compatibility could not be determined for N endpoints"*, never *"no breaking changes detected"*.
- **FR-6.5** Every `IndeterminateRegion` names the JSON pointer and the depth limit in force, so the report explains itself without reference to configuration.
- **FR-6.6** Every `RiskReport` carries a `scope_statement` field recording that the verdict describes the two supplied documents, not the deployed API.

## Non-functional requirements

### NFR-1 Determinism

- **NFR-1.1** Identical input produces byte-identical output, including ordering, across repeated runs.
- **NFR-1.2** No wall-clock time, random seed, or set-iteration order may influence output.
- **NFR-1.3** Verified by running the full fixture corpus 10 times and comparing serialised output.

### NFR-2 Auditability

- **NFR-2.1** Every finding traces to a named rule in the published rule set.
- **NFR-2.2** The rule set is data, not code branches, so it can be reviewed by a non-programmer.

### NFR-3 Safety

- **NFR-3.1** The deterministic core performs no network access.
- **NFR-3.2** Specification content never reaches a model prompt as instructions — only structured findings do. This makes the core immune to prompt injection via spec descriptions.
- **NFR-3.3** From M2, sandboxed execution runs with no network, a read-only root filesystem, all capabilities dropped, a non-root user, and explicit CPU, memory, PID and wall-clock limits.

### NFR-4 Graceful degradation

- **NFR-4.1** If the language model is unavailable, the report renders with deterministic findings and a template narrative.
- **NFR-4.2** Model failure is never a pipeline failure.

### NFR-5 Quality bars

- **NFR-5.1** Type checking and lint pass on every commit.
- **NFR-5.2** Test coverage on the comparison and scoring modules is at least 90%.
- **NFR-5.3** Every public function carries a docstring stating its contract.

## Technology constraints

Fixed by human decision; an agent may not vary these without approval.

| Area | Decision |
| --- | --- |
| Language floor | **Python `>=3.12`** — `requires-python = ">=3.12"` |
| Development and CI pin | **3.13** |
| CI test matrix | 3.12, 3.13 |
| Backend | Python, FastAPI |
| Comparison and scoring | Deterministic, no LLM in the verdict path |
| Orchestration | Plain Python. **No LangGraph in the MVP** |
| Storage | SQLite with SQLAlchemy initially; Postgres-compatible schema |
| Isolation | Docker, from M2 only |
| Frontend | React with TypeScript, **deferred to M5** |
| Testing | pytest |

**On the Python version.** The floor is `>=3.12`, not `>=3.14`. 3.12 supplies everything this project actually needs — PEP 695 generics, `Self`, and the improved error messages — while keeping the tool installable in the CI images and runtimes where it is most likely to be embedded. Pinning the floor at 3.14 would buy nothing the code uses and would exclude environments for no gain, and a brand-new minor version is the likeliest place to hit a gap in Pydantic, SQLAlchemy, or OpenAPI tooling. The host happens to run 3.14; that is a fact about the host, not a requirement, and the floor must not be derived from it. 3.14 remains supported — it simply is not required.
