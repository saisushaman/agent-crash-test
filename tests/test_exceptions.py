"""The exception hierarchy — the *fatal* mechanism of AGENTS.md rule 7.

When one of these is raised, no report is produced. They are distinct from the
indeterminate mechanism, where a report IS produced and says what it could not
determine.
"""

from __future__ import annotations

import pytest

from agent_crash_test.exceptions import (
    AgentCrashTestError,
    EmptySpecError,
    NonCanonicalValueError,
    SpecError,
    SpecFormatError,
    SpecParseError,
    SpecValidationError,
    UnsupportedSpecError,
)

FATAL = [
    SpecParseError,
    SpecFormatError,
    UnsupportedSpecError,
    EmptySpecError,
]


@pytest.mark.parametrize("error_type", FATAL)
def test_fatal_errors_derive_from_the_base(error_type: type[SpecError]) -> None:
    assert issubclass(error_type, SpecError)
    assert issubclass(error_type, AgentCrashTestError)


def test_non_canonical_value_error_derives_from_the_base() -> None:
    assert issubclass(NonCanonicalValueError, AgentCrashTestError)
    assert not issubclass(NonCanonicalValueError, SpecError)


@pytest.mark.parametrize("error_type", FATAL)
def test_every_fatal_error_names_the_offending_file(error_type: type[SpecError]) -> None:
    """FR-5.7: the user must know which of the two documents to fix."""
    error = error_type("proposed", "something went wrong")
    assert error.source == "proposed"
    assert "proposed" in str(error)
    assert "something went wrong" in str(error)


def test_source_distinguishes_original_from_proposed() -> None:
    assert SpecParseError("original", "bad indent").source == "original"
    assert SpecParseError("proposed", "bad indent").source == "proposed"


def test_validation_error_carries_every_pointer() -> None:
    """FR-5.4: one run surfaces the whole problem, not only the first pointer."""
    error = SpecValidationError(
        "original",
        "document violates the OpenAPI schema",
        ("#/paths", "#/components/schemas/User"),
    )
    assert error.pointers == ("#/paths", "#/components/schemas/User")
    assert "#/paths" in str(error)
    assert "#/components/schemas/User" in str(error)


def test_validation_error_with_no_pointers_still_explains_itself() -> None:
    error = SpecValidationError("proposed", "invalid", ())
    assert "no pointers reported" in str(error)


def test_errors_are_raisable_and_catchable_as_the_base() -> None:
    with pytest.raises(AgentCrashTestError):
        raise EmptySpecError("original", "zero paths")


def test_empty_spec_is_an_error_not_an_empty_result() -> None:
    """FR-5.5: 'nothing to compare' must never read as 'nothing wrong'."""
    with pytest.raises(SpecError) as caught:
        raise EmptySpecError("proposed", "the document declares no paths")
    assert caught.value.source == "proposed"
