#!/usr/bin/env python3
"""Probe every GET endpoint in the Swagger spec and report what this key can reach.

Which endpoints answer depends entirely on the claims attached to the API key,
and the API does not publish that mapping -- a 403 is the only way to find out.
Run this after any credential or claim change to get the real access map.

    python scripts/probe_access.py
    python scripts/probe_access.py --markdown > docs/access-map.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ceojuice import CeoJuiceClient, CeoJuiceError  # noqa: E402

# Live values from the sandbox demo DB, used to fill path templates. Override
# any of these if you point the probe at a different dataset.
SAMPLES = {
    "{customerNumber}": "BANKOFAMER",
    "{callNumber}": "1140",
    "{callId}": "1043",
    "{equipmentNumber}": "12345",
    "{serialNumber}": "27V02385",
    "{invoiceNumber}": "1",
    "{id}": "1",
    "{itemNumber}": "1",
    "{orderNumber}": "108",
    "{SOID}": "8",
    "{poNumber}": "1",
    "{email}": "sample@example.com",
    "{key}": "States",
    "{modelId}": "1",
    "{customerId}": "1",
    "{externalRef}": "1",
    "{sinceTime}": "2026-01-01T00:00:00",
}


def load_spec(base_url: str) -> dict:
    cached = Path(__file__).resolve().parent.parent / "docs" / "swagger.json"
    if cached.exists():
        return json.loads(cached.read_text())
    url = base_url.rstrip("/") + "/swagger/v1/swagger.json"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true", help="emit a markdown table")
    args = ap.parse_args()

    client = CeoJuiceClient()
    claims = client.claims()
    spec = load_spec(client.base_url)

    results = []
    for path, ops in sorted(spec["paths"].items()):
        if "get" not in ops or path.startswith("/swagger"):
            continue
        concrete = path
        for token, value in SAMPLES.items():
            concrete = concrete.replace(token, value)
        if "{" in concrete:
            continue  # unknown template we have no sample for
        try:
            client.get(concrete)
            status, note = 200, ""
        except CeoJuiceError as exc:
            status, note = exc.status, exc.body.strip().replace("\n", " ")[:90]
        except Exception as exc:  # network/parse trouble
            status, note = 0, str(exc)[:90]
        results.append((status, path, note))

    key = claims.get("CustomerName", "?")
    api_key_id = claims.get("ApiKeyId", "?")

    if args.markdown:
        print(f"# Access map\n\nKey `{api_key_id}` ({key}) against `{client.base_url}`.\n")
        print("| Status | Endpoint | Note |")
        print("| --- | --- | --- |")
        for status, path, note in sorted(results):
            print(f"| {status} | `{path}` | {note} |")
    else:
        print(f"Key {api_key_id} ({key}) against {client.base_url}\n")
        for status, path, note in sorted(results):
            label = "OK " if status == 200 else str(status)
            print(f"  {label:4} {path}  {note}")

    tally = Counter(status for status, _, _ in results)
    print("\n" + ", ".join(f"{code}: {n}" for code, n in sorted(tally.items())))
    granted = sorted(c for c, v in claims.items() if c.startswith("Claims_") and v == "true")
    print(f"\nClaims granted ({len(granted)}):")
    for claim in granted:
        print("  - " + claim.replace("Claims_", ""))
    return 0


if __name__ == "__main__":
    if not os.environ.get("CEOJUICE_USERNAME"):
        print("Set CEOJUICE_USERNAME / CEOJUICE_PASSWORD first.", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main())
