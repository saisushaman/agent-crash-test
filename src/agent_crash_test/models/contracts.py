"""The six data contracts, plus IndeterminateRegion.

Every model is frozen, so no stage can mutate another stage's output — a
precondition of determinism (NFR-1).

Ordering is applied **at construction**, not at serialisation (AC-0.2). A model
built from shuffled input is already canonical, so determinism does not depend on
remembering to sort before writing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_crash_test.models.enums import (
    Band,
    ChangeType,
    Comparability,
    HttpMethod,
    IndeterminateReason,
    NarrativeSource,
    ParameterLocation,
    Resolution,
    Severity,
    SourceFormat,
    SpecVersion,
)

SCOPE_STATEMENT = (
    "This result describes the two specification documents supplied. It does not "
    "describe the API actually running in production. If the original document has "
    "drifted from the deployed service, this verdict is correct about the documents "
    "and may be wrong about reality."
)


class Frozen(BaseModel):
    """Base for every contract: immutable, strict, no undeclared fields."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=False)


def _method_key(method: HttpMethod | None) -> str:
    """Sort key for an optional method. `None` sorts first, for whole-path changes."""
    return "" if method is None else method.value


class OpenAPISpec(Frozen):
    """The raw document as loaded, before normalisation. Exists only inside Intake."""

    source: str
    raw: dict[str, Any]
    version: SpecVersion
    source_format: SourceFormat
    path: Path


class SchemaProperty(Frozen):
    """One leaf of a request or response schema, flattened to a dotted path."""

    name: str
    schema_type: str
    format: str | None = None
    required: bool = False
    nullable: bool = False
    enum_values: tuple[str, ...] | None = None
    resolution: Resolution = Resolution.RESOLVED
    cycle_origin: str | None = None


class Parameter(Frozen):
    """A request parameter. Direction of change is side-dependent; see rules.py."""

    name: str
    location: ParameterLocation
    required: bool = False
    schema_type: str = "string"
    format: str | None = None
    enum_values: tuple[str, ...] | None = None
    nullable: bool = False


class Endpoint(Frozen):
    path: str
    method: HttpMethod
    operation_id: str | None = None
    parameters: tuple[Parameter, ...] = ()
    request_body: tuple[SchemaProperty, ...] = ()
    request_required: bool = False
    responses: dict[str, tuple[SchemaProperty, ...]] = Field(default_factory=dict)
    deprecated: bool = False

    @field_validator("parameters", mode="after")
    @classmethod
    def _sort_parameters(cls, value: tuple[Parameter, ...]) -> tuple[Parameter, ...]:
        return tuple(sorted(value, key=lambda p: (p.location.value, p.name)))

    @field_validator("request_body", mode="after")
    @classmethod
    def _sort_request_body(cls, value: tuple[SchemaProperty, ...]) -> tuple[SchemaProperty, ...]:
        return tuple(sorted(value, key=lambda p: p.name))

    @field_validator("responses", mode="after")
    @classmethod
    def _sort_responses(
        cls, value: dict[str, tuple[SchemaProperty, ...]]
    ) -> dict[str, tuple[SchemaProperty, ...]]:
        return {
            status: tuple(sorted(props, key=lambda p: p.name))
            for status, props in sorted(value.items())
        }


class Inventory(Frozen):
    """The normalised, version-agnostic representation.

    Every stage after Intake consumes this and nothing else.
    """

    endpoints: tuple[Endpoint, ...] = ()
    spec_version: SpecVersion
    title: str
    api_version: str

    @field_validator("endpoints", mode="after")
    @classmethod
    def _sort_endpoints(cls, value: tuple[Endpoint, ...]) -> tuple[Endpoint, ...]:
        return tuple(sorted(value, key=lambda e: (e.path, e.method.value)))


class Change(Frozen):
    """One detected difference, classified and justified."""

    type: ChangeType
    severity: Severity
    path: str
    method: HttpMethod | None = None
    target: str | None = None
    before: str | None = None
    after: str | None = None
    detail: str
    rule_id: str
    rationale: Annotated[str, Field(min_length=1)]
    comparability: Comparability = Comparability.PROVEN


class IndeterminateRegion(Frozen):
    """A region whose comparison could not be completed.

    Its presence bars a definitive verdict for the endpoint containing it
    (AGENTS.md rule 6).
    """

    path: str
    method: HttpMethod | None = None
    pointer: str
    reason: IndeterminateReason
    depth_limit: int


class TestResults(Frozen):
    """Sandboxed test execution results.

    Placeholder: M2 specifies its fields. Declared here only because RiskReport
    references it. No fields are invented ahead of that specification.
    """


class Decision(Frozen):
    """A recorded human approval decision.

    Placeholder: M4 specifies its fields. Declared here only because RiskReport
    references it. No fields are invented ahead of that specification.
    """


class RiskReport(Frozen):
    """The artifact a human approves against."""

    schema_version: str = "1"
    original_title: str
    original_api_version: str
    proposed_api_version: str
    changes: tuple[Change, ...] = ()
    breaking_count: int = 0
    compatible_count: int = 0
    informational_count: int = 0
    score: int = 0
    band: Band = Band.NONE
    indeterminate: tuple[IndeterminateRegion, ...] = ()
    scope_statement: Annotated[str, Field(min_length=1)] = SCOPE_STATEMENT
    test_results: TestResults | None = None
    narrative: str | None = None
    safer_alternative: str | None = None
    narrative_source: NarrativeSource = NarrativeSource.UNAVAILABLE
    decision: Decision | None = None

    @field_validator("changes", mode="after")
    @classmethod
    def _sort_changes(cls, value: tuple[Change, ...]) -> tuple[Change, ...]:
        return tuple(sorted(value, key=lambda c: (c.path, _method_key(c.method), c.type.value)))

    @field_validator("indeterminate", mode="after")
    @classmethod
    def _sort_indeterminate(
        cls, value: tuple[IndeterminateRegion, ...]
    ) -> tuple[IndeterminateRegion, ...]:
        return tuple(sorted(value, key=lambda r: (r.path, _method_key(r.method), r.pointer)))
