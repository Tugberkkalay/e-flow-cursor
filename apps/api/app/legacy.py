from __future__ import annotations

from typing import Any


def adapt_legacy_node(node: dict[str, Any]) -> dict[str, Any]:
    """Compatibility shim for future node preset migrations."""
    legacy_version = node.get("version", 1)
    if legacy_version <= 1:
        return node
    adapted = dict(node)
    adapted.setdefault("config", {})
    adapted["config"].setdefault("adapter_notice", "legacy_adapter_stub_applied")
    return adapted
