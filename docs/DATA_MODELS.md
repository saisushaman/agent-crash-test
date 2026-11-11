# DATA MODELS

Pydantic models. Every model is immutable (`frozen=True`) so that no stage can mutate another stage's output — a precondition of determinism (NFR-1).

## OpenAPISpec

The raw document as loaded, before normalisation. Exists only inside Intake.

| Field | Type | Notes |
| --- | --- | --- |
| `source` | `Literal["original", "proposed"]` | Which input this is; named in every error |
| `raw` | `dict` | Parsed document |
| `version` | `Literal["3.0", "3.1"]` | Detected from the `openapi` field |
| `source_format` | `Literal["yaml", "json"]` | Detected by content, not extension |
| `path` | `Path` | Origin file, for error messages |

## Inventory

The normalised, version-agnostic representation. **Every stage after Intake consumes this and nothing else.**

| Field | Type | Notes |
| --- | --- | --- |
| `endpoints` | `tuple[Endpoint, ...]` | Sorted by `(path, method)` for stable ordering |
| `spec_version` | `Literal["3.0", "3.1"]` | Retained only to classify version-attributable differences |
| `title` | `str` | From `info.title` |
| `api_version` | `str` | From `info.version` |

## Endpoint

| Field | Type | Notes |
| --- | --- | --- |
| `path` | `str` | Templated, e.g. `/users/{id}` |
| `method` | `HttpMethod` | Enum, upper case |
| `operation_id` | `str \| None` | Not required and not relied upon |
| `parameters` | `tuple[Parameter, ...]` | Sorted by `(location, name)` |
| `request_body` | `tuple[SchemaProperty, ...]` | Flattened; empty when absent |
| `request_required` | `bool` | Whether the body itself is required |
| `responses` | `Mapping[str, tuple[SchemaProperty, ...]]` | Keyed by status code |
| `deprecated` | `bool` | Informational only |

## Parameter

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `str` | |
| `location` | `Literal["path", "query", "header", "cookie"]` | `in` is reserved in Python |
| `required` | `bool` | Path parameters are always `True` |
| `schema_type` | `str` | Normalised JSON Schema type |
| `format` | `str \| None` | e.g. `int64`, `date-time` |
| `enum_values` | `tuple[str, ...] \| None` | Direction depends on side: see *The compatibility perspective* |
| `nullable` | `bool` | Normalises 3.0 `nullable` and 3.1 `type: [x, "null"]` |

## SchemaProperty

One leaf of a request or response schema, flattened to a dotted path so that nested changes compare without tree-walking in the differ.

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `str` | Dotted, e.g. `user.address.city` |
| `schema_type` | `str` | |
| `format` | `str \| None` | |
| `required` | `bool` | |
| `nullable` | `bool` | |
| `enum_values` | `tuple[str, ...] \| None` | |
| `resolution` | `Literal["resolved","recursive","depth_exceeded"]` | Defaults to `resolved`; see *Schema resolution and indeterminate results* |
| `cycle_origin` | `str \| None` | For `recursive`, the pointer the cycle returns to |

## Change

The output of the differ. One record per detected difference.

| Field | Type | Notes |
| --- | --- | --- |
| `type` | `ChangeType` | Closed enum, 14 members |
| `severity` | `Literal["breaking", "compatible", "informational"]` | From the rule set |
| `path` | `str` | Endpoint path |
| `method` | `HttpMethod \| None` | `None` for whole-path changes |
| `target` | `str \| None` | Parameter or property name, when applicable |
| `before` | `str \| None` | Prior value, rendered |
| `after` | `str \| None` | Proposed value, rendered |
| `detail` | `str` | Human-readable, generated deterministically — never by a model |
| `rule_id` | `str` | e.g. `R-001` |
| `rationale` | `str` | Why this severity; from the rule set. Never empty |
| `comparability` | `Literal["proven","unproven"]` | `proven` when the before/after pair matched the ordering table or a subset test. `unproven` when the two types are incomparable and conservative breaking was applied |

## RiskReport

| Field | Type | Notes |
| --- | --- | --- |
| `schema_version` | `str` | The report format's own version |
| `original_title` | `str` | |
| `original_api_version` | `str` | |
| `proposed_api_version` | `str` | |
| `changes` | `tuple[Change, ...]` | Stable order: path, method, change type |
| `breaking_count` | `int` | |
| `compatible_count` | `int` | |
| `informational_count` | `int` | |
| `score` | `int` | 0–100, deterministic |
| `band` | `Literal["none","low","medium","high","critical","indeterminate"]` | `indeterminate` whenever `indeterminate` is non-empty, regardless of score |
| `indeterminate` | `tuple[IndeterminateRegion, ...]` | Endpoints whose comparison could not be completed |
| `scope_statement` | `str` | Fixed text stating the verdict describes the supplied documents, not the deployed API. Travels with the artifact |
| `test_results` | `TestResults \| None` | M2; `None` until then |
| `narrative` | `str \| None` | Optional, model-generated or template |
| `safer_alternative` | `str \| None` | Optional, model-generated |
| `narrative_source` | `Literal["model","template","unavailable"]` | Makes model involvement explicit to the reader |
| `decision` | `Decision \| None` | M4 |

`score` and `band` are computed **before** the optional fields are populated, and are never recomputed afterwards.

`test_results` and `decision` are typed against `TestResults` and `Decision`, which remain **empty frozen placeholders** until M2 and M4 specify their fields. No field is invented ahead of its milestone.

## Canonical JSON serialisation

Determinism is only meaningful against a defined canonical form, so there is exactly one. Implemented in `src/agent_crash_test/serialization.py`.

| Aspect | Rule |
| --- | --- |
| Key order | Sorted lexicographically at every nesting level |
| Collection order | Applied at construction, not at serialisation — an in-memory model is already canonical |
| Enums | Lower-case string value, never an integer or object |
| Numbers | Integers only. No float appears anywhere in a report; a ratio is an integer percentage |
| Strings | UTF-8, non-ASCII preserved, not escaped |
| Absent values | Explicit `null`, never an omitted key, so key sets are identical across reports |
| Indentation | 2 spaces |
| Item separator | `","` |
| Key separator | `": "` |
| Trailing whitespace | **None.** No line may end in whitespace |

The item separator is `","` and not `", "`. Under indentation Python's `json` emits the item separator immediately before the newline, so `", "` would leave trailing whitespace on every line — noisy in diffs and easy to corrupt in transit. A test asserts no line carries trailing whitespace; it is a requirement, not an artefact of the chosen separator.

The no-float rule is **enforced, not documented**: `canonical_json` walks the structure and raises `NonCanonicalValueError` on the first float, naming its path. Float summation is order-dependent, which would make a score non-deterministic in exactly the way the architecture forbids.

## Change types and severity rules

The 14 initial types. Severity is data, reviewable without reading code (NFR-2.2).

### The compatibility perspective

Direction alone does not determine severity. **Which side of the call the change sits on** determines what direction means.

| Side | Breaking direction | Why |
| --- | --- | --- |
| **Request parameters** | The server accepts **fewer** inputs | A client sending what it always sent is now rejected |
| **Response schemas** | The server may return **more** kinds of output | A client is handed a value it has no branch for |

Both reduce to one principle: **a change is breaking when the other side must handle something it did not have to handle before.** For requests that means a smaller accepted set; for responses, a larger returned set.

R-005 and R-012 govern request parameters. R-007 and R-014 govern responses.

### Breaking — an existing client can stop working

| Rule | Type | Condition | Rationale |
| --- | --- | --- | --- |
| R-001 | `endpoint_removed` | A `(path, method)` in original is absent from proposed | Clients calling it receive 404 |
| R-002 | `method_removed` | The path survives, that method does not | Clients using that verb receive 405 |
| R-003 | `required_param_added` | A required parameter exists only in proposed | Existing calls omit it and are rejected |
| R-004 | `param_removed` | A parameter exists only in original | Clients still sending it may be rejected; its behaviour is gone |
| R-005 | `param_type_narrowed` | A request parameter's accepted value set **shrinks**: `int64`→`int32`, `number`→`integer`, `enum_values` loses a member, `nullable` true→false, optional→required on an existing parameter, or any type change that is not provably widening | Requests that were valid are now rejected |
| R-006 | `response_schema_field_removed` | A response property exists only in original | Clients reading that field break |
| R-007 | `response_type_widened` | A response property's set of possible values **grows**: `nullable` false→true, `enum_values` gains a member, `integer`→`number`, `int32`→`int64`, or any response type change that is not provably narrowing | Clients are handed values they have no branch for. A reader cannot refuse what the server sends |
| R-008 | `success_status_removed` | A 2xx status in original is absent from proposed | Clients branching on it break |

### Compatible — additive, existing clients unaffected

| Rule | Type | Condition | Rationale |
| --- | --- | --- | --- |
| R-009 | `endpoint_added` | A `(path, method)` exists only in proposed | No existing client calls it |
| R-010 | `optional_param_added` | A non-required parameter exists only in proposed | Existing calls remain valid |
| R-011 | `response_field_added` | A response property exists only in proposed | Clients ignore unknown fields |
| R-012 | `param_type_widened` | A request parameter's accepted value set **grows**, provably: `int32`→`int64`, `integer`→`number`, `enum_values` gains a member, `nullable` false→true, or required→optional | Every request that was valid remains valid |
| R-014 | `response_type_narrowed` | A response property's possible values are a provable **subset** of the original: `nullable` true→false, `enum_values` loses a member, `number`→`integer`, `int64`→`int32` | Every value the client could already handle, it can still handle. The server returns less, never something new |

### Informational — no contract effect

| Rule | Type | Condition | Rationale |
| --- | --- | --- | --- |
| R-013 | `description_changed` | Only `description`, `summary`, `deprecated`, or metadata differs | Documentation only. Also absorbs differences attributable solely to the 3.0-versus-3.1 version gap (FR-5.6) |

### Classifying direction

Direction must be **proved**, never assumed. The classifier holds one ordering table of type and format pairs (`int32` < `int64` < `number`; `nullable` false < true; required < optional) plus enum subset comparison. The same table serves both sides; only the direction that counts as safe differs.

| Side | Compatible when | Breaking when |
| --- | --- | --- |
| Request parameter | The pair is a **widening** step, or the before enum is a subset of the after enum → R-012 | Anything else → R-005 |
| Response property | The pair is a **narrowing** step, or the after enum is a subset of the before enum → R-014 | Anything else → R-007 |

### Incomparable changes and what "breaking" then means

Some pairs are neither widening nor narrowing. `string`→`boolean` is the clearest case: neither set of values contains the other, so no subset relation exists in either direction.

These are classified **breaking** — R-005 on a request, R-007 on a response — and carry `comparability: "unproven"`.

**The distinction must be stated honestly in the rationale.** An incomparable change is not literally a narrowing or a widening, and the report must not claim it is. The rationale reads *"compatibility could not be proven: `string` and `boolean` are not comparable"*, never *"the accepted value set shrank."* The verdict is conservative because the tool cannot prove safety, which is a different claim from proving harm — and a reviewer deciding whether to dismiss the finding needs to know which one they are looking at.

The conservative default itself is deliberate: an unprovable change called breaking costs a reviewer one dismissal, while one called compatible costs a production incident.

### Scoring

| Severity | Points each |
| --- | --- |
| `breaking` | 25 |
| `compatible` | 1 |
| `informational` | 0 |

Score is `min(100, sum)`. Bands: 0 → `none`, 1–9 → `low`, 10–24 → `medium`, 25–49 → `high`, 50+ → `critical`. **Any `breaking` change forces at least `high`** (FR-3.4), so a single breaking change cannot be averaged away by compatible ones.

## Schema resolution and indeterminate results

Resolution happens entirely in Intake; no `$ref` survives into `Inventory`. Resolution has **three** outcomes, and only the first two permit a definitive verdict.

| Outcome | `resolution` | Verdict permitted? | Meaning |
| --- | --- | --- | --- |
| Resolved | `resolved` | Yes | Fully expanded, nothing elided |
| Recognised cycle | `recursive` | Yes | A genuine self-reference, detected on the resolution stack and truncated at the cycle point. Supported, expected, not an error |
| Depth exceeded | `depth_exceeded` | **No** | Nesting passed the configured limit (default 8) without a cycle being detected. The schema is deeper than the tool handles |

The distinction is the point. A recognised cycle is **understood** — the tool knows exactly what it elided and why, both documents elide identically, and recursion alone never registers as a change. A depth-exceeded node is **not understood**: the tool stopped looking and does not know what lies beyond.

### The indeterminacy rule

**A `depth_exceeded` node must never yield a definitive compatibility verdict for the endpoint containing it.** Reporting "no breaking changes" about a subtree that was never examined is the single most damaging thing this tool could do.

`SchemaProperty` therefore carries:

| Field | Type | Notes |
| --- | --- | --- |
| `resolution` | `Literal["resolved","recursive","depth_exceeded"]` | Defaults to `resolved` |
| `cycle_origin` | `str \| None` | For `recursive`, the pointer the cycle returns to |

And a new record, `IndeterminateRegion`:

| Field | Type | Notes |
| --- | --- | --- |
| `path` | `str` | Endpoint path |
| `method` | `HttpMethod \| None` | |
| `pointer` | `str` | JSON pointer to the node that could not be resolved |
| `reason` | `Literal["depth_exceeded","unsupported_construct"]` | |
| `depth_limit` | `int` | The limit in force, so the report is self-explaining |

`RiskReport` gains:

| Field | Type | Notes |
| --- | --- | --- |
| `indeterminate` | `tuple[IndeterminateRegion, ...]` | Empty when every schema resolved cleanly |

Consequences, all enforced by test:

1. If `indeterminate` is non-empty, `band` is **`indeterminate`**, regardless of score. It is a distinct band, not a severity level, and it is never `none`.
2. No endpoint named in `indeterminate` may carry a `compatible` conclusion.
3. Report wording must say *"compatibility could not be determined for N endpoints"* — never *"no breaking changes detected."*
4. The depth limit is identical for both documents. Comparing at different depths would be meaningless.

External `$ref`s do not produce an indeterminate result: they raise `UnsupportedSpecError` and produce no report at all (FR-5.3). `unsupported_construct` is reserved for constructs discovered mid-resolution that the normaliser cannot represent.

### Resolved decisions

- **`param_type_changed` is split** into `param_type_widened` (compatible, R-012) and `param_type_narrowed` (breaking, R-005), approved 2026-11-11.
- **Recursion depth default is 8**, approved 2026-11-11, configurable, with depth-exceeded marked indeterminate rather than silently truncated.
- **R-007 inverted and the response side made symmetric**, approved 2026-11-11. The former `response_type_narrowed` (breaking) was wrong: for a response, *widening* is the breaking direction. R-007 is now `response_type_widened` (breaking) and R-014 `response_type_narrowed` (compatible) was added. **The type count is 14.**
- **Incomparable type changes** stay conservatively breaking but are marked `comparability: "unproven"`, so the report never claims a narrowing it cannot demonstrate.
