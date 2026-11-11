"""The rule set, as data.

NFR-2.2 requires the rule set be reviewable by a non-programmer, so severity
lives in tables here rather than distributed through `if` statements in a
classifier. M0 defines the data only; M1 implements the classifier that reads it.
"""

from __future__ import annotations

from typing import Literal, NamedTuple

from agent_crash_test.models.enums import ChangeType, Severity

Side = Literal["request", "response"]
Direction = Literal["widened", "narrowed"]


class Rule(NamedTuple):
    rule_id: str
    change_type: ChangeType
    severity: Severity
    rationale: str


RULES: tuple[Rule, ...] = (
    # --- Breaking: an existing client can stop working ---
    Rule(
        "R-001",
        ChangeType.ENDPOINT_REMOVED,
        Severity.BREAKING,
        "Clients calling it receive 404.",
    ),
    Rule(
        "R-002",
        ChangeType.METHOD_REMOVED,
        Severity.BREAKING,
        "Clients using that verb receive 405.",
    ),
    Rule(
        "R-003",
        ChangeType.REQUIRED_PARAM_ADDED,
        Severity.BREAKING,
        "Existing calls omit it and are rejected.",
    ),
    Rule(
        "R-004",
        ChangeType.PARAM_REMOVED,
        Severity.BREAKING,
        "Clients still sending it may be rejected; its behaviour is gone.",
    ),
    Rule(
        "R-005",
        ChangeType.PARAM_TYPE_NARROWED,
        Severity.BREAKING,
        "Requests that were valid are now rejected: the server accepts fewer inputs.",
    ),
    Rule(
        "R-006",
        ChangeType.RESPONSE_SCHEMA_FIELD_REMOVED,
        Severity.BREAKING,
        "Clients reading that field break.",
    ),
    Rule(
        "R-007",
        ChangeType.RESPONSE_TYPE_WIDENED,
        Severity.BREAKING,
        "Clients are handed values they have no branch for. A reader cannot refuse "
        "what the server sends.",
    ),
    Rule(
        "R-008",
        ChangeType.SUCCESS_STATUS_REMOVED,
        Severity.BREAKING,
        "Clients branching on it break.",
    ),
    # --- Compatible: additive, existing clients unaffected ---
    Rule(
        "R-009",
        ChangeType.ENDPOINT_ADDED,
        Severity.COMPATIBLE,
        "No existing client calls it.",
    ),
    Rule(
        "R-010",
        ChangeType.OPTIONAL_PARAM_ADDED,
        Severity.COMPATIBLE,
        "Existing calls remain valid.",
    ),
    Rule(
        "R-011",
        ChangeType.RESPONSE_FIELD_ADDED,
        Severity.COMPATIBLE,
        "Clients ignore unknown fields.",
    ),
    Rule(
        "R-012",
        ChangeType.PARAM_TYPE_WIDENED,
        Severity.COMPATIBLE,
        "Every request that was valid remains valid.",
    ),
    Rule(
        "R-014",
        ChangeType.RESPONSE_TYPE_NARROWED,
        Severity.COMPATIBLE,
        "Every value the client could already handle, it can still handle. The server "
        "returns less, never something new.",
    ),
    # --- Informational: no contract effect ---
    Rule(
        "R-013",
        ChangeType.DESCRIPTION_CHANGED,
        Severity.INFORMATIONAL,
        "Documentation only. Also absorbs differences attributable solely to the "
        "3.0-versus-3.1 version gap.",
    ),
)

RULE_BY_TYPE: dict[ChangeType, Rule] = {rule.change_type: rule for rule in RULES}
RULE_BY_ID: dict[str, Rule] = {rule.rule_id: rule for rule in RULES}


# --- Per-side direction tables -------------------------------------------------
#
# Which direction is safe depends on the side of the call. Both reduce to: a
# change is breaking when the other side must handle something it did not have to
# handle before (AGENTS.md rule 4).

DIRECTION_TO_TYPE: dict[tuple[Side, Direction], ChangeType] = {
    ("request", "widened"): ChangeType.PARAM_TYPE_WIDENED,  # R-012, compatible
    ("request", "narrowed"): ChangeType.PARAM_TYPE_NARROWED,  # R-005, breaking
    ("response", "widened"): ChangeType.RESPONSE_TYPE_WIDENED,  # R-007, breaking
    ("response", "narrowed"): ChangeType.RESPONSE_TYPE_NARROWED,  # R-014, compatible
}

#: The change type applied when direction cannot be proved in either direction.
#: Conservatively breaking on both sides, and always marked `unproven`.
UNPROVEN_FALLBACK: dict[Side, ChangeType] = {
    "request": ChangeType.PARAM_TYPE_NARROWED,
    "response": ChangeType.RESPONSE_TYPE_WIDENED,
}

#: Ordered widening steps, read as `(narrower, broader)`.
#: A pair found here is a proven widening; reversed, a proven narrowing.
#: One table serves both sides — only which direction counts as safe differs.
WIDENING_STEPS: tuple[tuple[str, str], ...] = (
    ("int32", "int64"),
    ("int64", "number"),
    ("integer", "number"),
    ("int32", "number"),
)

#: Scoring weights. Integers only: float summation is order-dependent, which
#: would destroy determinism (AGENTS.md rule 3).
SEVERITY_POINTS: dict[Severity, int] = {
    Severity.BREAKING: 25,
    Severity.COMPATIBLE: 1,
    Severity.INFORMATIONAL: 0,
}

#: Rationale wording for an incomparable pair. It must state that compatibility
#: could not be proven, never assert a narrowing or widening that was not
#: demonstrated (AGENTS.md rule 5).
UNPROVEN_RATIONALE = (
    "Compatibility could not be proven: {before} and {after} are not comparable, so "
    "neither value set contains the other. Classified breaking conservatively."
)
