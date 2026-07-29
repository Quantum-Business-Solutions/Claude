# Claude

## CEO Juice Client API

A Python client for the CEO Juice Service Call Client API, which exposes
e-automate data — customers, contacts, equipment, service calls, sales orders,
contracts, invoices, and meter readings.

See **[docs/CONNECTION.md](docs/CONNECTION.md)** for the connection guide: how
auth works, what the API key can reach, how ID136 and ID634 map onto endpoints,
and the two gotchas that will bite a sync job (the `ListsAndCodes` 403 family and
the silent 7-day `Recentchanges` cap).

### Setup

No dependencies beyond the standard library.

```bash
cp .env.example .env      # then fill in credentials
export CEOJUICE_USERNAME=... CEOJUICE_PASSWORD=...
```

### Usage

```python
from ceojuice import CeoJuiceClient

client = CeoJuiceClient()          # reads CEOJUICE_* from the environment

client.claims()                    # what this API key is allowed to do
client.customer("BANKOFAMER")      # single record
client.get_list("CallTypes")       # lookups, routed around the 403 family

for equipment in client.active_equipment(page_size=100):
    ...                            # paging handled transparently
```

Delta sync, guarded against the silent 7-day cap:

```python
from datetime import datetime, timedelta, timezone

since = datetime.now(timezone.utc) - timedelta(days=1)
for call in client.recent_changes("ServiceCall", since):
    ...
```

Create a service call (the ID136 ticketing path — serial or equipment number is
required):

```python
client.add_service_call(
    description="Paper jam",
    equipment_number="12345",
    reference_call_identifier="INC0987",   # your ticket ID, for matching back
)
```

### Mapping access for a credential

Which endpoints answer depends on the claims attached to the key, and that
mapping is not documented — a 403 is the only way to discover it. To regenerate
the map after any credential or claim change:

```bash
python scripts/probe_access.py                        # human-readable
python scripts/probe_access.py --markdown > docs/access-map.md
```

Current output: [docs/access-map.md](docs/access-map.md).
