# ACCEPTANCE CRITERIA

Measurable exit conditions. Each traces to a requirement in [REQUIREMENTS.md](REQUIREMENTS.md). "Done" means the stated evidence exists, not that code was written.

## M0

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-0.1 | Six data contracts frozen and importable | `Inventory`, `Endpoint`, `Parameter`, `SchemaProperty`, `Change`, `RiskReport` are frozen Pydantic models | FR-4.1 |
| AC-0.2 | Ordering applied at construction, not serialisation | A model built from shuffled input is already canonically ordered | NFR-1.2 |
| AC-0.3 | Canonical JSON serialisation defined and enforced | Same object, 10 serialisations, byte-identical; keys sorted, enums as strings, no floats | NFR-1.1 |
| AC-0.4 | `RiskReport` round-trips to JSON and back | Equality holds after a serialise/parse cycle | FR-4.1 |
| AC-0.5 | 14 change types present as a closed enum with severity data | Enum has 14 members; every member has a rule id and rationale | FR-2.2 |
| AC-0.6 | Three representative fixture pairs exist | One breaking, one compatible, one identical, each expressible in `Change` records | — |
| AC-0.7 | `RiskReport` carries `scope_statement` | Field present and non-empty on every report | FR-6.6 |
| AC-0.8 | CI runs lint, type check and pytest on push | Green run on the default branch | NFR-5.1 |

## M1

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-1.1 | All 14 change types detected and correctly classified | One passing fixture per type, asserting the full `Change` record | FR-2.2, FR-2.3 |
| AC-1.1b | Perspective applied correctly on both sides | Request widening compatible, response widening breaking, and the reverse for each | FR-2.7 |
| AC-1.1c | Incomparable changes marked `unproven` and worded honestly | Fixtures 16 and 17: severity breaking, `comparability: "unproven"`, rationale says compatibility could not be proven | FR-2.8 |
| AC-1.2 | OpenAPI 3.0 and 3.1 both parse to equivalent `Inventory` | Fixture pair differing only in spec version yields zero breaking changes | FR-1.2, FR-5.6 |
| AC-1.3 | YAML and JSON both accepted, detected by content | Same spec in both formats yields identical `Inventory` | FR-1.3 |
| AC-1.4 | Differ performs no I/O, network or model calls | No such imports in the module; asserted by review and an import test | FR-2.5 |
| AC-1.5 | Every `Change` carries a non-empty `rationale` and `rule_id` | Property test over the whole corpus | FR-2.4, NFR-2.1 |
| AC-1.6 | `classify(x, x)` is empty for every fixture | Property test over all 27 fixtures | FR-2.6 |
| AC-1.7 | Determinism | Corpus run 10 times, serialised output byte-identical | NFR-1.1, NFR-1.3 |
| AC-1.8 | All error conditions raise their typed error, naming the file | Fixtures 21-25, one per error class | FR-5.1 to FR-5.8 |
| AC-1.9 | Coverage on `differ` and `intake` at least 90% | Coverage report in CI | NFR-5.2 |
| AC-1.10 | Recursive schema resolves without error | Fixture 19: self-referencing `Node` schema in both documents yields 0 changes | FR-1.6 |
| AC-1.11 | Depth-exceeded yields `band: indeterminate` | Fixture 20: 12-level nesting, no cycle, depth limit 8 | FR-1.7, FR-6.2 |
| AC-1.12 | No endpoint in `indeterminate` carries a compatible conclusion | Property test over fixtures 19-20 | FR-6.3 |
| AC-1.13 | Report wording never claims "no breaking changes" when indeterminate | String assertion on rendered report | FR-6.4 |

## M2

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-2.1 | A deliberately failing suite is reported as failing | Fixture repo with a known-failing test | FR-3.1 |
| AC-2.2 | Network access is denied inside the sandbox | Escape fixture attempting egress fails closed | NFR-3.3 |
| AC-2.3 | Host filesystem is unreachable | Escape fixture attempting host read fails closed | NFR-3.3 |
| AC-2.4 | Resource limits enforced | Fixtures exceeding CPU, memory and wall-clock are each terminated | NFR-3.3 |
| AC-2.5 | Container runs as non-root with no capabilities | Asserted by inspecting the running container in a test | NFR-3.3 |

## M3

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-3.1 | Score and band deterministic | 10 runs, byte-identical | NFR-1.1 |
| AC-3.2 | Any single breaking change yields band at least `high` | Property test over the corpus | FR-3.4 |
| AC-3.3 | Report renders with the model disabled | `narrative_source` is `"template"`, all findings present | NFR-4.1 |
| AC-3.4 | Model failure does not fail the pipeline | Fault-injection test with the model raising | NFR-4.2 |
| AC-3.5 | Model stages receive no raw spec content | Prompt-construction test asserts only structured findings are passed | NFR-3.2 |

## M4

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-4.1 | No change applied without a recorded decision | Attempt without a decision is rejected | FR-4.3 |
| AC-4.2 | Decisions immutable | Update attempt on a recorded decision is rejected | FR-4.4 |
| AC-4.3 | Approval endpoint authenticated | Unauthenticated request rejected | FR-4.3 |

## M5

| ID | Criterion | Evidence | Traces |
| --- | --- | --- | --- |
| AC-5.1 | Reviewer approves or rejects without touching the API | Walkthrough against a seeded report | FR-4.3 |

## Fixture corpus — the M1 gate

27 before/after pairs. Fixtures 1-14 cover one change type each; 15-17 pin the direction and comparability edge cases; 18-20 cover format, version and identity; 21-22 cover schema resolution; 23-27 cover the error paths. Each is a directory holding `original.yaml` (or `.json`), `proposed.yaml`, and `expected.json` with the full expected `Change` list.

Three of these (18, 19 and one of 1-14) are the representative pairs built in M0.

| # | Fixture | Exercises | Expected |
| --- | --- | --- | --- |
| 1 | `endpoint_removed` | `DELETE /users/{id}` in original only | 1 breaking, R-001 |
| 2 | `method_removed` | `/users` keeps GET, loses POST | 1 breaking, R-002 |
| 3 | `required_param_added` | New required query param `tenant` | 1 breaking, R-003 |
| 4 | `param_removed` | Query param `sort` dropped | 1 breaking, R-004 |
| 5 | `param_type_narrowed` | Query param `page` `int64` to `int32` | 1 breaking, R-005 |
| 6 | `response_schema_field_removed` | `user.email` dropped from 200 | 1 breaking, R-006 |
| 7 | `response_type_widened` | `user.age` non-nullable to nullable | 1 breaking, R-007 |
| 8 | `success_status_removed` | 202 removed, 200 retained | 1 breaking, R-008 |
| 9 | `endpoint_added` | New `GET /health` | 1 compatible, R-009 |
| 10 | `optional_param_added` | New optional query param `limit` | 1 compatible, R-010 |
| 11 | `response_field_added` | `user.created_at` added to 200 | 1 compatible, R-011 |
| 12 | `param_type_widened` | Query param `page` `int32` to `int64` | 1 compatible, R-012 |
| 13 | `description_changed` | Only `summary` text differs | 1 informational, R-013 |
| 14 | `response_type_narrowed` | `user.status` enum loses a member | 1 compatible, R-014 |
| 15 | `response_enum_widened` | `user.status` enum **gains** a member | 1 breaking, R-007 |
| 16 | `param_type_unrelated` | Request `flag` string to boolean | 1 breaking, R-005, `comparability: "unproven"` |
| 17 | `response_type_unrelated` | Response `code` string to boolean | 1 breaking, R-007, `comparability: "unproven"` |
| 18 | `identical` | Byte-identical files | 0 changes |
| 19 | `format_parity` | Same API, YAML original and JSON proposal | 0 changes |
| 20 | `version_gap_30_31` | 3.0 original, 3.1 proposal, same API | 0 breaking; version-attributable differences informational |
| 21 | `recursive_cycle` | Self-referencing `Node` schema in both documents | 0 changes, `band` not `indeterminate` |
| 22 | `depth_exceeded` | 12-level nesting, no cycle, depth limit 8 | `band: indeterminate`, 1 `IndeterminateRegion`, no compatible verdict |
| 23 | `malformed_yaml` | Broken indentation | `SpecParseError`, names file and line |
| 24 | `not_openapi` | Valid YAML, no `openapi` field | `SpecFormatError` |
| 25 | `swagger_2` | Swagger 2.0 document | `UnsupportedSpecError` |
| 26 | `external_ref` | `$ref` to `./common.yaml` | `UnsupportedSpecError`, never fetched |
| 27 | `empty_spec` | `paths: {}` | `EmptySpecError`, **not** an empty change list |

### What the corpus is actually proving

**The perspective rules (5, 7, 12, 14, 15).** These four pairs are the heart of the gate, because they are mirror images and a classifier that confuses the two sides will pass some and fail others:

| | Request | Response |
| --- | --- | --- |
| **Widened** | 12 → compatible | 7, 15 → **breaking** |
| **Narrowed** | 5 → **breaking** | 14 → compatible |

A classifier that applies one direction rule to both sides passes exactly half of these. That is the failure this table is designed to catch.

**Honest uncertainty (16, 17).** Both are incomparable type changes on opposite sides. Both must be breaking, both must carry `comparability: "unproven"`, and neither rationale may claim a narrowing or widening. The assertion is on the rationale text, not just the severity.

**The safety floor (18, 21, 22, 26, 27).** 18 proves no spurious changes are invented. 27 proves "nothing to compare" is never reported as "nothing wrong." 21 and 22 prove the distinction the project turns on: a *recognised* cycle still permits a verdict, *depth exceeded* must not — fixture 22 fails if the report says anything resembling "no breaking changes detected." 26 proves an external reference is rejected rather than fetched, keeping the deterministic core offline (NFR-3.1).
