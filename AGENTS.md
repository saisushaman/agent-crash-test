# AGENTS.md

Engineering constraints for anyone — human or agent — writing code in this repository.

These are **invariants, not preferences.** Code that violates one is wrong even if it passes its tests. This file does not restate the documentation; it names the rules and points at where each is specified.

## Where the specifications live

| Document | Authority over |
| --- | --- |
| `docs/INTENT.md` | Product scope. **Source of truth.** |
| `docs/REQUIREMENTS.md` | Functional and non-functional requirements (FR / NFR ids) |
| `docs/ARCHITECTURE.md` | Pipeline, module layout, dependency direction |
| `docs/DATA_MODELS.md` | Models, the 14 change types, severity rules, resolution semantics |
| `docs/MILESTONES.md` | What is in each milestone, and its gate |
| `docs/ACCEPTANCE_CRITERIA.md` | What "done" means, and the fixture corpus |

Read the relevant one before changing behaviour it governs. Where this file and a specification disagree, the specification wins — and the disagreement is a bug worth reporting.

## Non-negotiable constraints

**1. The verdict is deterministic. An LLM may never determine or modify it.**
Classification, severity, scoring, and band are computed by rules alone. A model may write narrative prose and propose a safer alternative; both are optional, non-blocking, and may not alter any field the deterministic stages produced. If removing every model stage changes a verdict, the change is wrong.

**2. No network access in the deterministic core. No external reference fetching, ever.**
Intake, differ, scorer, and report assembler make no network calls. An external `$ref` is rejected, never resolved. Fetching it would make the verdict depend on something outside the two supplied documents.

**3. Canonical JSON only. No floating-point values anywhere in reports or scoring.**
Sorted keys, defined collection ordering applied at construction, enums as lower-case strings, explicit `null` over omitted keys. Scores are integers. Float summation is order-dependent, which would destroy determinism — so floats are excluded by rule, not by habit.

**4. Compatibility direction is evaluated separately for requests and responses.**
They are not symmetric and must not share a direction rule. Requests break when the server accepts **fewer** inputs; responses break when the server may return **more** kinds of output. One direction rule applied to both sides is the specific defect this rule exists to prevent. See *The compatibility perspective* in `docs/DATA_MODELS.md`.

**5. Incomparable changes are breaking, and marked unproven.**
When neither value set contains the other, classify breaking and set `comparability: "unproven"`. The rationale must say compatibility could not be proven. It must never assert a narrowing or widening that was not demonstrated. Failing to prove safety is a different claim from proving harm, and the report must not blur them.

**6. Recursion and depth limits follow the documented indeterminate behaviour.**
A recognised cycle is supported and still permits a verdict. A node exceeding the depth limit does not: it is recorded as an `IndeterminateRegion`, the band becomes `indeterminate`, and no affected endpoint may be called compatible. Never collapse these two cases. See FR-1.6, FR-1.7, FR-6.

**7. Never silently ignore a parsing error, an unsupported reference, or incomplete analysis.**
Two distinct mechanisms, and they must not be conflated:

- **Fatal — raise a typed exception.** Malformed YAML or JSON, structural validation failures, unsupported spec versions, unresolvable local `$ref`s, external `$ref`s, and empty specifications. Each names the offending file (`original` or `proposed`). **No report is produced.** See FR-5.
- **Indeterminate — produce a report that says so.** A schema exceeding the depth limit is **not** a fatal parsing error. It is recorded as an `IndeterminateRegion`, forces `band: indeterminate`, and bars a compatible verdict for the affected endpoint. A report *is* produced, and it states plainly what could not be determined. See FR-6.

Do not route a depth-limit case through the exception path, and do not let one degrade into a partial report. Neither mechanism may ever resolve to a silent pass: no error path returns a partial or empty report, and an empty change list must only ever mean "nothing changed" — never "we could not look."

**8. Tests and fixtures must cover every rule and both directions.**
Each of the 14 rules has at least one fixture asserting the complete `Change` record, not just a count. The request/response mirror-image set must stay intact: a classifier that confuses the two sides passes exactly half of it. New rule, new fixture, in the same change.

**9. `docs/INTENT.md` is the source of truth for scope.**
Its out-of-scope list is binding. Do not widen scope, add a dependency, or introduce infrastructure to make a task easier. Scope changes are human decisions.

## Requires human approval before you proceed

Stop and ask. Do not resolve these by choosing the reading that unblocks you.

- Any change to the change-type enum, severity rules, or the data contracts
- Anything touching scope, the out-of-scope list, or a new dependency
- Any behaviour not covered by a requirement, where you would otherwise invent the answer
- Loosening a constraint in this file

## Working rules

- No task is complete without test evidence. "It compiles" is not evidence.
- Every implementation task carries written acceptance criteria before it starts.
- Record ambiguity as an open question in `docs/MILESTONES.md`. Never resolve it by invention.
- Dependency direction is strictly downward: `differ` imports `models`, never `intake`. Nothing imports `narrative`.
- Do not create a repository, configure a remote, or push without explicit instruction.

## When a constraint makes a task hard

That is usually the constraint working. The determinism, offline, and no-float rules exist because this tool's output is meant to be trusted enough to approve a production deployment against. Raise the conflict rather than routing around it.
