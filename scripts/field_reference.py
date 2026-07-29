#!/usr/bin/env python3
"""Build a field-level reference for every object the API exposes.

Swagger gives names and types. It does not tell you which fields actually carry
data, which matters more in practice -- plenty are defined, returned on every
record, and always null. So this samples live records per entity and reports a
fill rate alongside each field.

    python scripts/field_reference.py --json docs/field-reference.json
    python scripts/field_reference.py --markdown docs/FIELDS.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ceojuice import CeoJuiceClient, CeoJuiceError  # noqa: E402

# entity label -> (response schema, sampling route, paged?)
ENTITIES = {
    "Customer": ("Customer", "/api/Customer", True),
    "Contact": ("Contact", "/api/Contact", True),
    "Contract": ("Contract", "/api/Contract/active", True),
    "ContractDetail": ("ContractDetail", None, False),
    "Equipment": ("Equipment", "/api/Equipment/AllActive", True),
    "ServiceCall": ("ServiceCall", "/api/ServiceCall/AllOpen", True),
    "SalesOrder": ("SalesOrder", "/api/SalesOrder/AllOpen", True),
    "SOOrderDetail": ("SOOrderDetail", None, False),
    "Invoice": ("Invoice", None, False),
    "InvoiceDetail": ("InvoiceDetail", None, False),
    "ModelMeters": ("ModelMeters", None, False),
    "PrintReleafUsageRecord": ("PrintReleafUsageRecord", None, False),
    "Item": ("Item", None, False),
    "Make": ("Make", "/api/Item/Makes", False),
    "Model": ("Model", "/api/Item/Models", False),
    "CallType": ("CallType", "/api/ServiceCall/CallTypes", False),
    "State": ("State", "/api/Customer/States", False),
    "Term": ("Term", "/api/Customer/Terms", False),
    "PriceLevel": ("PriceLevel", "/api/Customer/PriceLevels", False),
    "SOOrderType": ("SOOrderType", "/api/SalesOrder/OrderTypes", False),
    "Priority": ("Priority", "/api/ServiceCall/Priorities", False),
    "ProblemCode": ("ProblemCode", "/api/ServiceCall/ProblemCodes", False),
    "RepairCode": ("RepairCode", "/api/ServiceCall/RepairCodes", False),
    "SLACode": ("SLACode", "/api/ServiceCall/SLACodes", False),
    "NoteType": ("NoteType", "/api/ServiceCall/NoteTypes", False),
    "OnHoldCode": ("OnHoldCode", "/api/ServiceCall/OnHoldCodes", False),
    "CancelCode": ("CancelCode", "/api/ServiceCall/CancelCodes", False),
    # Write-side payload shapes -- no route to sample, spec only.
    "NewServiceCallDto": ("NewServiceCallDto", None, False),
    "ImpSalesOrderDetailDto": ("ImpSalesOrderDetailDto", None, False),
    "CreateCustomerRequest": ("CreateCustomerRequest", None, False),
    "CreateContactRequest": ("CreateContactRequest", None, False),
}

SAMPLE_SIZE = 200


def field_type(spec: dict, prop: dict) -> str:
    if "$ref" in prop:
        return prop["$ref"].rsplit("/", 1)[-1]
    base = prop.get("type", "object")
    if base == "array":
        items = prop.get("items", {})
        inner = items.get("$ref", "").rsplit("/", 1)[-1] or items.get("type", "any")
        return f"{inner}[]"
    fmt = prop.get("format")
    if fmt in ("date-time", "date"):
        return "datetime"
    if fmt in ("double", "float", "decimal"):
        return "decimal"
    if fmt in ("int32", "int64"):
        return "int"
    return base


def is_filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    ap.add_argument("--markdown", type=Path)
    args = ap.parse_args()

    spec = json.loads((Path(__file__).resolve().parent.parent / "docs" / "swagger.json").read_text())
    schemas = spec["components"]["schemas"]
    client = CeoJuiceClient()

    report = {}
    for label, (schema_name, route, paged) in ENTITIES.items():
        props = (schemas.get(schema_name) or {}).get("properties") or {}
        samples: list[dict] = []
        note = ""
        if route:
            try:
                if paged:
                    samples = list(client.paginate(route, page_size=100, max_pages=2))
                else:
                    payload = client.get(route)
                    samples = payload if isinstance(payload, list) else [payload]
            except CeoJuiceError as exc:
                note = f"sampling failed: HTTP {exc.status}"
        else:
            note = "no list route — shape from spec only"
        samples = [s for s in samples if isinstance(s, dict)][:SAMPLE_SIZE]

        fields = []
        for name, prop in props.items():
            entry = {
                "field": name,
                "type": field_type(spec, prop),
                "nullable": bool(prop.get("nullable")),
            }
            if samples:
                filled = sum(1 for s in samples if is_filled(s.get(name)))
                entry["fill_pct"] = round(100 * filled / len(samples))
                example = next(
                    (s.get(name) for s in samples if is_filled(s.get(name))), None
                )
                if isinstance(example, (dict, list)):
                    example = f"<{type(example).__name__}>"
                elif isinstance(example, str):
                    example = example.strip()[:40]
                entry["example"] = example
            fields.append(entry)

        report[label] = {
            "schema": schema_name,
            "route": route,
            "sampled": len(samples),
            "note": note,
            "field_count": len(fields),
            "fields": fields,
        }
        print(
            f"  {label:24} {len(fields):>4} fields  sampled {len(samples):>4}  {note}",
            file=sys.stderr,
        )

    if args.json:
        args.json.write_text(json.dumps(report, indent=2, default=str))
        print(f"wrote {args.json}", file=sys.stderr)

    if args.markdown:
        lines = [
            "# Field reference",
            "",
            "Every object the CEO Juice Client API exposes, with the share of live",
            "sampled records where each field is actually populated. Generated by",
            "`scripts/field_reference.py` — regenerate rather than editing by hand.",
            "",
            f"Fill rates come from up to {SAMPLE_SIZE} live records per entity. A low",
            "rate is not necessarily a gap, but a 0% field is one you cannot build on.",
            "",
        ]
        for label, info in report.items():
            lines.append(f"## {label}")
            lines.append("")
            bits = [f"`{info['field_count']}` fields"]
            if info["route"]:
                bits.append(f"route `{info['route']}`")
            if info["sampled"]:
                bits.append(f"sampled {info['sampled']} records")
            if info["note"]:
                bits.append(f"_{info['note']}_")
            lines.append(" · ".join(bits))
            lines.append("")
            has_fill = any("fill_pct" in f for f in info["fields"])
            if has_fill:
                lines.append("| Field | Type | Filled | Example |")
                lines.append("| --- | --- | --- | --- |")
                for f in info["fields"]:
                    ex = f.get("example")
                    ex = "" if ex is None else f"`{ex}`"
                    pct = f.get("fill_pct")
                    lines.append(
                        f"| `{f['field']}` | {f['type']} | "
                        f"{'—' if pct is None else str(pct) + '%'} | {ex} |"
                    )
            else:
                lines.append("| Field | Type |")
                lines.append("| --- | --- |")
                for f in info["fields"]:
                    lines.append(f"| `{f['field']}` | {f['type']} |")
            lines.append("")
        args.markdown.write_text("\n".join(lines))
        print(f"wrote {args.markdown}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
