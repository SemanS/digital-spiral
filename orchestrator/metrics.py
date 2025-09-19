from __future__ import annotations

from typing import Any, Mapping

_BASELINES = {
    "comment": 90,
    "transition": 30,
    "set-labels": 45,
    "link": 60,
}


def estimate_savings(action_kind: str, context: Mapping[str, Any] | None = None) -> int:
    """Estimate seconds saved for a given action kind.

    Parameters
    ----------
    action_kind:
        The type of action executed (comment, transition, etc.).
    context:
        Optional information about the action, not currently used but reserved
        for future heuristics.
    """

    base = _BASELINES.get(action_kind, 30)
    bundle = 1
    if context:
        bundle = int(context.get("bundle_size", 1)) or 1
    seconds = int(base * bundle)
    return max(seconds, 0)
