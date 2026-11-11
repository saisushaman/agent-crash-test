"""AC-0.1, AC-0.2, AC-0.5, AC-0.7 — the data contracts."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from agent_crash_test.models import (
    DIRECTION_TO_TYPE,
    RULE_BY_TYPE,
    RULES,
    SCOPE_STATEMENT,
    UNPROVEN_FALLBACK,
    Change,
    ChangeType,
    Comparability,
    Endpoint,
    HttpMethod,
    IndeterminateRegion,
    Inventory,
    Parameter,
    ParameterLocation,
    Resolution,
    RiskReport,
    SchemaProperty,
    Severity,
    SpecVersion,
)
from agent_crash_test.models.rules import Side

CONTRACTS = [Inventory, Endpoint, Parameter, SchemaProperty, Change, RiskReport]


def _endpoint(path: str, method: HttpMethod = HttpMethod.GET, **kw: object) -> Endpoint:
    return Endpoint(path=path, method=method, **kw)


def _change(path: str, change_type: ChangeType, **kw: object) -> Change:
    rule = RULE_BY_TYPE[change_type]
    return Change(
        type=change_type,
        severity=rule.severity,
        path=path,
        detail=f"{change_type.value} at {path}",
        rule_id=rule.rule_id,
        rationale=rule.rationale,
        **kw,
    )


# --- AC-0.1 six contracts frozen and importable -------------------------------


@pytest.mark.parametrize("model", CONTRACTS)
def test_contract_is_frozen(model: type[BaseModel]) -> None:
    assert model.model_config["frozen"] is True


def test_frozen_models_reject_mutation() -> None:
    endpoint = _endpoint("/users")
    with pytest.raises(ValidationError):
        endpoint.path = "/other"  # type: ignore[misc]


def test_contracts_forbid_undeclared_fields() -> None:
    with pytest.raises(ValidationError):
        Parameter(name="x", location=ParameterLocation.QUERY, nonsense=1)  # type: ignore[call-arg]


# --- AC-0.2 ordering applied at construction ----------------------------------


def test_endpoints_sorted_at_construction() -> None:
    inventory = Inventory(
        endpoints=(
            _endpoint("/zebra"),
            _endpoint("/users", HttpMethod.POST),
            _endpoint("/users", HttpMethod.GET),
            _endpoint("/alpha"),
        ),
        spec_version=SpecVersion.V3_1,
        title="t",
        api_version="1",
    )
    assert [(e.path, e.method.value) for e in inventory.endpoints] == [
        ("/alpha", "get"),
        ("/users", "get"),
        ("/users", "post"),
        ("/zebra", "get"),
    ]


def test_parameters_sorted_by_location_then_name() -> None:
    endpoint = _endpoint(
        "/users",
        parameters=(
            Parameter(name="sort", location=ParameterLocation.QUERY),
            Parameter(name="id", location=ParameterLocation.PATH, required=True),
            Parameter(name="limit", location=ParameterLocation.QUERY),
        ),
    )
    assert [(p.location.value, p.name) for p in endpoint.parameters] == [
        ("path", "id"),
        ("query", "limit"),
        ("query", "sort"),
    ]


def test_response_properties_and_statuses_sorted() -> None:
    endpoint = _endpoint(
        "/users",
        responses={
            "404": (SchemaProperty(name="message", schema_type="string"),),
            "200": (
                SchemaProperty(name="user.name", schema_type="string"),
                SchemaProperty(name="user.email", schema_type="string"),
            ),
        },
    )
    assert list(endpoint.responses) == ["200", "404"]
    assert [p.name for p in endpoint.responses["200"]] == ["user.email", "user.name"]


def test_request_body_properties_sorted_at_construction() -> None:
    endpoint = _endpoint(
        "/users",
        method=HttpMethod.POST,
        request_body=(
            SchemaProperty(name="user.name", schema_type="string"),
            SchemaProperty(name="user.address.city", schema_type="string"),
            SchemaProperty(name="user.email", schema_type="string"),
        ),
        request_required=True,
    )
    assert [p.name for p in endpoint.request_body] == [
        "user.address.city",
        "user.email",
        "user.name",
    ]


def test_changes_sorted_by_path_method_type() -> None:
    report = RiskReport(
        original_title="t",
        original_api_version="1",
        proposed_api_version="2",
        changes=(
            _change("/zebra", ChangeType.ENDPOINT_ADDED, method=HttpMethod.GET),
            _change("/alpha", ChangeType.ENDPOINT_REMOVED, method=HttpMethod.POST),
            _change("/alpha", ChangeType.ENDPOINT_REMOVED, method=HttpMethod.GET),
        ),
    )
    assert [(c.path, c.method.value if c.method else "") for c in report.changes] == [
        ("/alpha", "get"),
        ("/alpha", "post"),
        ("/zebra", "get"),
    ]


def test_shuffled_input_yields_identical_model() -> None:
    """A model built from shuffled input is already canonical (AC-0.2)."""
    forward = Inventory(
        endpoints=(_endpoint("/a"), _endpoint("/b"), _endpoint("/c")),
        spec_version=SpecVersion.V3_1,
        title="t",
        api_version="1",
    )
    reverse = Inventory(
        endpoints=(_endpoint("/c"), _endpoint("/b"), _endpoint("/a")),
        spec_version=SpecVersion.V3_1,
        title="t",
        api_version="1",
    )
    assert forward == reverse


def test_indeterminate_regions_sorted() -> None:
    from agent_crash_test.models import IndeterminateReason

    report = RiskReport(
        original_title="t",
        original_api_version="1",
        proposed_api_version="2",
        indeterminate=(
            IndeterminateRegion(
                path="/z", pointer="#/b", reason=IndeterminateReason.DEPTH_EXCEEDED, depth_limit=8
            ),
            IndeterminateRegion(
                path="/a", pointer="#/a", reason=IndeterminateReason.DEPTH_EXCEEDED, depth_limit=8
            ),
        ),
    )
    assert [r.path for r in report.indeterminate] == ["/a", "/z"]


# --- AC-0.5 fourteen change types with severity data --------------------------


def test_change_type_enum_has_fourteen_members() -> None:
    assert len(ChangeType) == 14


def test_every_change_type_has_a_rule() -> None:
    assert set(RULE_BY_TYPE) == set(ChangeType)
    assert len(RULES) == 14


def test_every_rule_has_id_and_non_empty_rationale() -> None:
    for rule in RULES:
        assert rule.rule_id.startswith("R-")
        assert rule.rationale.strip()


def test_rule_ids_are_unique() -> None:
    ids = [rule.rule_id for rule in RULES]
    assert len(set(ids)) == len(ids)


def test_severity_distribution_matches_documentation() -> None:
    """8 breaking, 5 compatible, 1 informational (docs/DATA_MODELS.md)."""
    counts = {severity: 0 for severity in Severity}
    for rule in RULES:
        counts[rule.severity] += 1
    assert counts[Severity.BREAKING] == 8
    assert counts[Severity.COMPATIBLE] == 5
    assert counts[Severity.INFORMATIONAL] == 1


def test_rationale_is_required_and_non_empty() -> None:
    with pytest.raises(ValidationError):
        Change(
            type=ChangeType.ENDPOINT_REMOVED,
            severity=Severity.BREAKING,
            path="/users",
            detail="d",
            rule_id="R-001",
            rationale="",
        )


# --- AGENTS.md rule 4: the per-side direction tables --------------------------


def test_direction_table_is_side_dependent() -> None:
    """Requests break when accepting fewer; responses when returning more."""
    assert DIRECTION_TO_TYPE[("request", "narrowed")] == ChangeType.PARAM_TYPE_NARROWED
    assert DIRECTION_TO_TYPE[("request", "widened")] == ChangeType.PARAM_TYPE_WIDENED
    assert DIRECTION_TO_TYPE[("response", "widened")] == ChangeType.RESPONSE_TYPE_WIDENED
    assert DIRECTION_TO_TYPE[("response", "narrowed")] == ChangeType.RESPONSE_TYPE_NARROWED


def test_direction_severity_is_mirrored_across_sides() -> None:
    """The mirror image: the same direction has opposite severity per side."""
    assert RULE_BY_TYPE[DIRECTION_TO_TYPE[("request", "widened")]].severity is Severity.COMPATIBLE
    assert RULE_BY_TYPE[DIRECTION_TO_TYPE[("response", "widened")]].severity is Severity.BREAKING
    assert RULE_BY_TYPE[DIRECTION_TO_TYPE[("request", "narrowed")]].severity is Severity.BREAKING
    assert RULE_BY_TYPE[DIRECTION_TO_TYPE[("response", "narrowed")]].severity is Severity.COMPATIBLE


def test_unproven_fallback_is_breaking_on_both_sides() -> None:
    sides: tuple[Side, ...] = ("request", "response")
    for side in sides:
        assert RULE_BY_TYPE[UNPROVEN_FALLBACK[side]].severity is Severity.BREAKING


def test_comparability_defaults_to_proven() -> None:
    change = _change("/users", ChangeType.ENDPOINT_REMOVED)
    assert change.comparability is Comparability.PROVEN


def test_comparability_can_be_marked_unproven() -> None:
    change = _change("/users", ChangeType.PARAM_TYPE_NARROWED, comparability=Comparability.UNPROVEN)
    assert change.comparability is Comparability.UNPROVEN


# --- AC-0.7 scope statement ---------------------------------------------------


def test_report_carries_scope_statement_by_default() -> None:
    report = RiskReport(original_title="t", original_api_version="1", proposed_api_version="2")
    assert report.scope_statement == SCOPE_STATEMENT
    assert "not" in report.scope_statement and "production" in report.scope_statement


def test_scope_statement_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        RiskReport(
            original_title="t",
            original_api_version="1",
            proposed_api_version="2",
            scope_statement="",
        )


# --- resolution semantics (AGENTS.md rule 6) ----------------------------------


def test_resolution_defaults_to_resolved() -> None:
    assert SchemaProperty(name="a", schema_type="string").resolution is Resolution.RESOLVED


def test_recursive_and_depth_exceeded_are_distinct() -> None:
    """A recognised cycle and a depth-exceeded node must never collapse into one state."""
    values = [r.value for r in Resolution]
    assert len(set(values)) == len(values) == 3
    assert set(values) == {"resolved", "recursive", "depth_exceeded"}
