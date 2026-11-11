"""Typed errors for fatal input conditions.

Per AGENTS.md rule 7, these are the *fatal* mechanism: when one is raised, no
report is produced. They are distinct from the *indeterminate* mechanism, where
a report IS produced and states what could not be determined.

Every error names the offending file so the user knows which one to fix (FR-5.7).
"""

from __future__ import annotations

from typing import Literal

SpecSource = Literal["original", "proposed"]


class AgentCrashTestError(Exception):
    """Base for every error this tool raises deliberately."""


class SpecError(AgentCrashTestError):
    """A fatal problem with one of the two supplied specification documents."""

    def __init__(self, source: SpecSource, message: str) -> None:
        self.source: SpecSource = source
        self.message = message
        super().__init__(f"[{source}] {message}")


class SpecParseError(SpecError):
    """Malformed YAML or JSON (FR-5.1)."""


class SpecFormatError(SpecError):
    """Well-formed file, but not a recognisable OpenAPI document (FR-5.2)."""


class UnsupportedSpecError(SpecError):
    """Unsupported version, or an external reference (FR-5.3).

    External references are never fetched: fetching would put network access in
    the deterministic core (NFR-3.1).
    """


class SpecValidationError(SpecError):
    """Parses, but violates the OpenAPI schema (FR-5.4).

    Carries every offending JSON pointer rather than only the first, so one run
    surfaces the whole problem.
    """

    def __init__(self, source: SpecSource, message: str, pointers: tuple[str, ...]) -> None:
        self.pointers = pointers
        detail = ", ".join(pointers) if pointers else "no pointers reported"
        super().__init__(source, f"{message} ({detail})")


class EmptySpecError(SpecError):
    """Zero paths (FR-5.5).

    Never treated as "no endpoints, therefore no changes": an empty change list
    reads to a human as "this change is safe".
    """


class NonCanonicalValueError(AgentCrashTestError):
    """A value that cannot be canonically serialised reached the serialiser.

    In practice this means a float. Float summation is order-dependent, which
    would destroy determinism, so floats are excluded by rule (AGENTS.md rule 3).
    """
