"""Canonical JSON serialisation.

Determinism is only meaningful against a defined canonical form, so there is
exactly one (AGENTS.md rule 3):

* keys sorted lexicographically at every level
* enums as their lower-case string value
* explicit ``null``, never an omitted key, so key sets are stable across reports
* UTF-8 preserved, non-ASCII not escaped
* **no floating-point values anywhere**
* 2-space indent

Float summation is order-dependent, so a float in a report would make the score
non-deterministic in exactly the way the architecture forbids. Rather than trust
that no one introduces one, :func:`canonical_json` walks the structure and
raises. The rule is enforced, not documented.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from agent_crash_test.exceptions import NonCanonicalValueError

#: Separators chosen so no line carries trailing whitespace under ``indent``.
_SEPARATORS = (",", ": ")
_INDENT = 2


def _reject_floats(value: Any, pointer: str = "$") -> None:
    """Walk a JSON-able structure and raise on the first float found.

    ``bool`` is a subclass of ``int`` and is fine; ``float`` never is.
    """
    if isinstance(value, float):
        raise NonCanonicalValueError(
            f"float at {pointer}: {value!r}. Reports and scoring are integer-only, "
            "because float summation is order-dependent and would break determinism."
        )
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_floats(item, f"{pointer}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_floats(item, f"{pointer}[{index}]")


def to_canonical_dict(model: BaseModel) -> dict[str, Any]:
    """Render a model as a plain dict in canonical form.

    ``exclude_none`` is deliberately off: an omitted key and a null key are
    different documents, and stable key sets are part of the canonical form.
    """
    data = model.model_dump(mode="json", exclude_none=False)
    _reject_floats(data)
    return data


def canonical_json(model: BaseModel) -> str:
    """Serialise a model to the one canonical JSON form.

    Byte-identical for equal inputs, which is what the determinism check compares.
    """
    return json.dumps(
        to_canonical_dict(model),
        sort_keys=True,
        ensure_ascii=False,
        separators=_SEPARATORS,
        indent=_INDENT,
    )


def canonical_json_from_obj(obj: Any) -> str:
    """Canonical form for a plain structure, for fixtures and tests."""
    _reject_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=_SEPARATORS,
        indent=_INDENT,
    )
