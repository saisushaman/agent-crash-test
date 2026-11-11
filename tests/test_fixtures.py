"""AC-0.6 — the three representative fixture pairs.

M0 has no parser, so these tests do not compare specifications. They assert the
weaker thing M0 can honestly assert: that each fixture's expected result is
expressible in `Change` records, and that its rule and severity agree with the
rule set. A contract you cannot express a fixture against is not finished.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_crash_test.models import RULE_BY_ID, Change

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
REPRESENTATIVE = ["endpoint_removed", "endpoint_added", "identical"]


def _expected(name: str) -> list[dict[str, object]]:
    data = json.loads((FIXTURES / name / "expected.json").read_text(encoding="utf-8"))
    changes: list[dict[str, object]] = data["changes"]
    return changes


@pytest.mark.parametrize("name", REPRESENTATIVE)
def test_fixture_directory_is_complete(name: str) -> None:
    directory = FIXTURES / name
    for filename in ("original.yaml", "proposed.yaml", "expected.json"):
        assert (directory / filename).is_file(), f"{name}/{filename} missing"


@pytest.mark.parametrize("name", REPRESENTATIVE)
def test_expected_changes_are_expressible_as_change_records(name: str) -> None:
    for raw in _expected(name):
        change = Change.model_validate(raw)
        assert change.rationale.strip()


@pytest.mark.parametrize("name", REPRESENTATIVE)
def test_expected_rule_and_severity_agree_with_the_rule_set(name: str) -> None:
    for raw in _expected(name):
        change = Change.model_validate(raw)
        rule = RULE_BY_ID[change.rule_id]
        assert change.type is rule.change_type
        assert change.severity is rule.severity


def test_the_three_representatives_cover_breaking_compatible_and_identical() -> None:
    breaking = _expected("endpoint_removed")
    compatible = _expected("endpoint_added")
    identical = _expected("identical")

    assert [c["severity"] for c in breaking] == ["breaking"]
    assert [c["severity"] for c in compatible] == ["compatible"]
    assert identical == [], "the identical pair must expect no changes at all"


def test_identical_fixture_files_are_byte_identical() -> None:
    directory = FIXTURES / "identical"
    original = (directory / "original.yaml").read_bytes()
    proposed = (directory / "proposed.yaml").read_bytes()
    assert original == proposed


def test_changed_fixtures_actually_differ() -> None:
    for name in ("endpoint_removed", "endpoint_added"):
        directory = FIXTURES / name
        assert (directory / "original.yaml").read_bytes() != (
            directory / "proposed.yaml"
        ).read_bytes(), f"{name} pair is identical but expects a change"
