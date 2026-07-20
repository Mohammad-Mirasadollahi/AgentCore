"""Dynamic-dispatch synthesis with provenance (Wave 3).

When a call targets a base/interface type (or unresolved name matching a
base method) and a subclass defines the same method name, emit a probable
CALLS edge to the subclass method with metadata.provenance=dynamic_dispatch.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class SynthesizedCall:
    source_id: str
    target_id: str
    method_name: str
    via_type: str
    provenance: str = "dynamic_dispatch"


def synthesize_interface_dispatch(
    *,
    # id, name, qualified_name, kind
    symbols: list[tuple[str, str, str, str]],
    # child_id, parent_id (INHERITS_FROM)
    inherits: list[tuple[str, str]],
    # source_id, target_id, call_name
    calls: list[tuple[str, str, str]],
) -> list[SynthesizedCall]:
    by_id = {s[0]: s for s in symbols}
    children_of: dict[str, list[str]] = defaultdict(list)
    for child, parent in inherits:
        children_of[parent].append(child)

    # class_id -> {method_name: method_id}
    methods_by_class: dict[str, dict[str, str]] = defaultdict(dict)
    for sid, name, qn, kind in symbols:
        if kind != "method":
            continue
        # Heuristic owner: class whose qualified_name is a prefix of method qn
        for cid, _cn, cqn, ckind in symbols:
            if ckind == "class" and (qn.startswith(cqn + ".") or qn.startswith(cqn + "::")):
                methods_by_class[cid][name] = sid
                break
        else:
            # Fallback: "Class.method" in qualified_name
            if "." in qn:
                owner = qn.rsplit(".", 1)[0]
                for cid, cn, cqn, ckind in symbols:
                    if ckind == "class" and (cqn == owner or cn == owner.split(".")[-1]):
                        methods_by_class[cid][name] = sid
                        break

    out: list[SynthesizedCall] = []
    seen: set[tuple[str, str]] = set()

    for source_id, target_id, call_name in calls:
        short = call_name.split(".")[-1]
        base_ids: list[str] = []
        if target_id in children_of:
            base_ids.append(target_id)
        # call like Base.method
        if "." in call_name:
            type_part = call_name.rsplit(".", 1)[0]
            for sid, name, qn, kind in symbols:
                if kind == "class" and (name == type_part or qn.endswith("." + type_part) or qn == type_part):
                    base_ids.append(sid)
        # unresolved target name equals a class
        tsym = by_id.get(target_id)
        if tsym and tsym[3] == "class":
            base_ids.append(target_id)
        if str(target_id).startswith("unresolved:"):
            unresolved_name = str(target_id).split(":")[-1]
            for sid, name, qn, kind in symbols:
                if kind == "class" and name == unresolved_name:
                    base_ids.append(sid)

        for base_id in base_ids:
            base = by_id.get(base_id)
            via = base[1] if base else "base"
            for child_id in children_of.get(base_id, ()):
                mid = methods_by_class.get(child_id, {}).get(short)
                if not mid:
                    continue
                key = (source_id, mid)
                if key in seen or mid == target_id:
                    continue
                seen.add(key)
                out.append(
                    SynthesizedCall(
                        source_id=source_id,
                        target_id=mid,
                        method_name=short,
                        via_type=via,
                    )
                )
    return out
