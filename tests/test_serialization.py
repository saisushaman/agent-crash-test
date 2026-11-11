"""AC-0.3, AC-0.4 — canonical JSON and the round trip."""

from __future__ import annotations

import json

import pytest

from agent_crash_test.exceptions import NonCanonicalValueError
from agent_crash_test.models import (
    RULE_BY_TYPE,
    Band,
    Change,
    ChangeType,
    HttpMethod,
    IndeterminateReason,
    IndeterminateRegion,
    RiskReport,
    Severity,
)
from agent_crash_test.serialization import (
    canonical_json,
    canonical_json_from_obj,
    to_canonical_dict,
)


def _report() -> RiskReport:
    rule = RULE_BY_TYPE[ChangeType.ENDPOINT_REMOVED]
    return RiskReport(
        original_title="Users API",
        original_api_version="1.0.0",
        proposed_api_version="2.0.0",
        changes=(
            Change(
                type=ChangeType.ENDPOINT_REMOVED,
                severity=Severity.BREAKING,
                path="/users/{id}",
                method=HttpMethod.DELETE,
                before="DELETE /users/{id}",
                detail="Endpoint DELETE /users/{id} was removed.",
                rule_id=rule.rule_id,
                rationale=rule.rationale,
            ),
        ),
        breaking_count=1,
        score=25,
        band=Band.HIGH,
        indeterminate=(
            IndeterminateRegion(
                path="/users/{id}",
                method=HttpMethod.GET,
                pointer="#/components/schemas/Deep",
                reason=IndeterminateReason.DEPTH_EXCEEDED,
                depth_limit=8,
            ),
        ),
    )


# --- AC-0.3 canonical serialisation -------------------------------------------


def test_serialisation_is_byte_identical_across_ten_runs() -> None:
    report = _report()
    renders = {canonical_json(report) for _ in range(10)}
    assert len(renders) == 1


def test_equal_models_serialise_identically() -> None:
    assert canonical_json(_report()) == canonical_json(_report())


def test_keys_are_sorted_at_every_level() -> None:
    text = canonical_json(_report())
    loaded = json.loads(text)
    assert list(loaded) == sorted(loaded)
    for change in loaded["changes"]:
        assert list(change) == sorted(change)
    for region in loaded["indeterminate"]:
        assert list(region) == sorted(region)


def test_enums_serialise_as_lowercase_strings() -> None:
    loaded = json.loads(canonical_json(_report()))
    assert loaded["band"] == "high"
    assert loaded["changes"][0]["type"] == "endpoint_removed"
    assert loaded["changes"][0]["severity"] == "breaking"
    assert loaded["changes"][0]["method"] == "delete"
    assert loaded["changes"][0]["comparability"] == "proven"


def test_null_fields_are_present_not_omitted() -> None:
    """Stable key sets across reports: an omitted key and a null key differ."""
    loaded = json.loads(canonical_json(_report()))
    assert "test_results" in loaded
    assert loaded["test_results"] is None
    assert loaded["changes"][0]["after"] is None
    assert "after" in loaded["changes"][0]


def test_no_line_carries_trailing_whitespace() -> None:
    for line in canonical_json(_report()).splitlines():
        assert line == line.rstrip(), f"trailing whitespace: {line!r}"


def test_indent_is_two_spaces() -> None:
    lines = canonical_json(_report()).splitlines()
    indented = [line for line in lines if line.startswith(" ")]
    assert indented
    assert all((len(line) - len(line.lstrip(" "))) % 2 == 0 for line in indented)


def test_non_ascii_is_preserved_not_escaped() -> None:
    rule = RULE_BY_TYPE[ChangeType.DESCRIPTION_CHANGED]
    report = RiskReport(
        original_title="Café API — naïve",
        original_api_version="1",
        proposed_api_version="2",
        changes=(
            Change(
                type=ChangeType.DESCRIPTION_CHANGED,
                severity=Severity.INFORMATIONAL,
                path="/café",
                detail="Summary changed to “updated”.",
                rule_id=rule.rule_id,
                rationale=rule.rationale,
            ),
        ),
    )
    text = canonical_json(report)
    assert "Café API — naïve" in text
    assert "\\u" not in text


# --- AGENTS.md rule 3: no floats, enforced not documented ---------------------


def test_float_in_a_report_is_rejected() -> None:
    with pytest.raises(NonCanonicalValueError, match="float"):
        canonical_json_from_obj({"score": 25.0})


def test_nested_float_is_rejected_and_pointer_reported() -> None:
    with pytest.raises(NonCanonicalValueError, match=r"\$\.a\[1\]\.b"):
        canonical_json_from_obj({"a": [{"x": 1}, {"b": 0.5}]})


def test_bool_is_not_mistaken_for_a_float() -> None:
    assert "true" in canonical_json_from_obj({"flag": True})


def test_scores_are_integers() -> None:
    loaded = json.loads(canonical_json(_report()))
    assert isinstance(loaded["score"], int)
    assert not isinstance(loaded["score"], float)


# --- AC-0.4 round trip --------------------------------------------------------


def test_report_round_trips_through_json() -> None:
    report = _report()
    restored = RiskReport.model_validate(json.loads(canonical_json(report)))
    assert restored == report


def test_round_trip_is_stable_a_second_time() -> None:
    report = _report()
    once = RiskReport.model_validate(json.loads(canonical_json(report)))
    twice = RiskReport.model_validate(json.loads(canonical_json(once)))
    assert canonical_json(twice) == canonical_json(report)


def test_to_canonical_dict_matches_parsed_json() -> None:
    report = _report()
    assert to_canonical_dict(report) == json.loads(canonical_json(report))
