"""Closed enumerations.

Every member serialises as its lower-case string value, never as an integer or
an object (AGENTS.md rule 3).
"""

from __future__ import annotations

from enum import StrEnum


class HttpMethod(StrEnum):
    GET = "get"
    PUT = "put"
    POST = "post"
    DELETE = "delete"
    OPTIONS = "options"
    HEAD = "head"
    PATCH = "patch"
    TRACE = "trace"


class ParameterLocation(StrEnum):
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


class SpecVersion(StrEnum):
    V3_0 = "3.0"
    V3_1 = "3.1"


class SourceFormat(StrEnum):
    YAML = "yaml"
    JSON = "json"


class Resolution(StrEnum):
    """How far `$ref` resolution got for one schema node.

    `RECURSIVE` and `DEPTH_EXCEEDED` must never be conflated. A recognised cycle
    was elided deliberately and still permits a verdict; a depth-exceeded node
    was never examined and does not (AGENTS.md rule 6).
    """

    RESOLVED = "resolved"
    RECURSIVE = "recursive"
    DEPTH_EXCEEDED = "depth_exceeded"


class Severity(StrEnum):
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    INFORMATIONAL = "informational"


class Comparability(StrEnum):
    """Whether the direction of a type change was demonstrated.

    `UNPROVEN` means the tool failed to prove safety, which is a different claim
    from proving harm. The rationale must say so (AGENTS.md rule 5).
    """

    PROVEN = "proven"
    UNPROVEN = "unproven"


class Band(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INDETERMINATE = "indeterminate"


class IndeterminateReason(StrEnum):
    DEPTH_EXCEEDED = "depth_exceeded"
    UNSUPPORTED_CONSTRUCT = "unsupported_construct"


class NarrativeSource(StrEnum):
    MODEL = "model"
    TEMPLATE = "template"
    UNAVAILABLE = "unavailable"


class ChangeType(StrEnum):
    """The 14 change types. See docs/DATA_MODELS.md for conditions and rationale.

    Direction is side-dependent: a request breaks when the server accepts fewer
    inputs, a response when it may return more kinds of output (AGENTS.md rule 4).
    """

    # Breaking
    ENDPOINT_REMOVED = "endpoint_removed"
    METHOD_REMOVED = "method_removed"
    REQUIRED_PARAM_ADDED = "required_param_added"
    PARAM_REMOVED = "param_removed"
    PARAM_TYPE_NARROWED = "param_type_narrowed"
    RESPONSE_SCHEMA_FIELD_REMOVED = "response_schema_field_removed"
    RESPONSE_TYPE_WIDENED = "response_type_widened"
    SUCCESS_STATUS_REMOVED = "success_status_removed"
    # Compatible
    ENDPOINT_ADDED = "endpoint_added"
    OPTIONAL_PARAM_ADDED = "optional_param_added"
    RESPONSE_FIELD_ADDED = "response_field_added"
    PARAM_TYPE_WIDENED = "param_type_widened"
    RESPONSE_TYPE_NARROWED = "response_type_narrowed"
    # Informational
    DESCRIPTION_CHANGED = "description_changed"
