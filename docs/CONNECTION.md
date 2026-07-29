# CEO Juice Client API — connection guide

Notes from getting an authenticated connection working against the CEO Juice
Service Call Client API, which exposes e-automate data (customers, equipment,
service calls, sales orders, contracts, invoices, meter readings).

- **Base URL (dev/sandbox):** `https://devclientsapi.ceojuice.com`
- **Swagger UI:** `/swagger/index.html`
- **Machine-readable spec:** `/swagger/v1/swagger.json` — vendored at
  [`swagger.json`](swagger.json) (94 paths, `Service Call Client API 2026.07.27`)

Verified working 2026-07-29 with the `quantum` sandbox credentials.

## Authenticating

Two steps: trade username/password for a JWT, then bearer that JWT everywhere.

```bash
curl -X POST https://devclientsapi.ceojuice.com/api/Auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"quantum","password":"..."}'
# -> {"token":"eyJ...","expires":"2026-07-29T15:18:16.32Z"}

curl https://devclientsapi.ceojuice.com/api/Customer?pageSize=2 \
  -H "Authorization: Bearer eyJ..."
```

Tokens last about **6 hours**. `CeoJuiceClient` caches one and re-authenticates
a minute before expiry, so callers never think about it.

### The `eaapikey` header is not needed

Swagger declares two security schemes — `ApiKey` (an `eaapikey` header) and
`Bearer` — in a single requirement block, which reads as *both are mandatory*.
They are not. **Bearer alone works**; the JWT already embeds `ApiKeyId`, so the
token *is* the API key. Verified: `/api/Test` returns 200 with only the bearer
header, 401 with none.

## What the key can see

`GET /api/Test` returns the token's claim list — the authoritative answer for
what a given credential may do. The sandbox key resolves to:

| | |
| --- | --- |
| AccessKeyType | `AllAccess` |
| ApiKeyId | `10` |
| CustomerName | `ECI e-automate` |
| CustomerNumber / CustomerID | `DGI` / `47` |

with read on Customers, Contacts, Equipment, ServiceCalls, Inventory,
SalesOrders, Invoices, MeterReadings, Contracts, PrintReleaf; write on Contacts,
Customers, Inventory, ServiceCalls, SalesOrders, MeterReadings, APInvoice.

The sandbox holds the standard e-automate demo dataset — 160 customers, 1,109
active equipment records, 225 open service calls, 635 open sales orders — and is
static, with nothing modified since October 2025.

`scripts/probe_access.py` walks every documented GET and reports what actually
answers; [`access-map.md`](access-map.md) is its current output. Re-run it after
any claim change, because the endpoint→claim mapping is not published anywhere
and a 403 is the only way to discover it.

## Gotcha: the entire `/api/ListsAndCodes/*` family returns 403

All 19 `ListsAndCodes` routes are forbidden to this key, as are `/api/Branch`,
`/api/User/*`, and `/api/Process/GetProcessOutput`.

The lookups are not actually lost. Every one is **duplicated under a
domain-scoped route gated on the domain claim instead**, and those return 200 —
Swagger even says so ("Same data as /api/listsandcodes/X, gated on Claims_X").
So `/api/ListsAndCodes/CallTypes` is 403 while `/api/ServiceCall/CallTypes`
returns the same 26 rows.

| Lookup | Use this instead of `/api/ListsAndCodes/…` |
| --- | --- |
| CallTypes, ProblemCodes, RepairCodes, CancelCodes, OnHoldCodes, Priorities, NoteTypes, SLACodes | `/api/ServiceCall/<name>` |
| States, Countries, Terms, PriceLevels | `/api/Customer/<name>` |
| OrderTypes, OrderStatuses, ShipMethods | `/api/SalesOrder/<name>` |
| MeterTypes | `/api/MeterReadings/MeterTypes` |
| Makes, Models, ModelCategories | `/api/Item/<name>` |

`client.get_list("CallTypes")` resolves through this table, so callers never
have to remember which family works.

## Paging

List endpoints take `?page=N&pageSize=N` and answer:

```json
{"page": 1, "pageSize": 2, "totalCount": 160, "totalPages": 80, "items": [...]}
```

`client.paginate(path)` yields items across all pages and also tolerates the
handful of routes that ignore paging and return a bare array.

## Gotcha: `Recentchanges` silently caps at 7 days

Delta sync lives at `/api/<Entity>/Recentchanges/{sinceTime}` with `sinceTime`
formatted `yyyy-MM-ddTHH:mm:ss`, for Customer, Contact, Contract, Equipment,
Invoice, SalesOrder, and ServiceCall.

**The window is capped at 7 days, and exceeding it is not an error.** A
`sinceTime` of 30 days ago returns `{"totalCount": 0, "items": []}` with HTTP
200 — indistinguishable from "nothing changed". A nightly sync that misses a
week would quietly conclude the dataset is unchanged and skip real updates.

`client.recent_changes()` raises `ValueError` rather than let that happen. Poll
well inside the window, and fall back to a full pull if the last successful sync
is older than that.

## ID136 — API sync to ticketing systems

CEO Juice process **ID136** is the ticketing-sync side of this API. It is not a
literal endpoint; it maps onto the `ServiceCall` routes:

```python
client.add_service_call(
    description="Paper jam",
    equipment_number="12345",           # or serial_number=...
    reference_call_identifier="INC0987",  # your ticket ID, for matching back
    contact_name="John Crumpton",
    notes="Additional detail about the problem",
)
```

`serialNumber` **or** `equipmentNumber` is required — that is what binds the
call to a machine. Put your own system's ticket ID in
`referenceCallIdentifier` so the call can be reconciled later. Related:
`AddNote`, `CancelCall` (only valid before a technician is dispatched),
`ByCallNumber`, `AllOpen`, `Recentchanges`.

## ID634 — sales order import (the complicated one)

CEO Juice process **ID634** is the Sales Order Import Utility, surfaced as
`PUT /api/SalesOrder/AddOrder`. It is not a plain create — it is a staged batch
import:

1. The API writes **one row per order line** into the custom table
   `ZCJ_ImpSOOrderDetails`, all sharing a generated `SourceID`.
2. It invokes stored procedure `ZCJ_Event_634_Log` with that `SourceID`.
3. That procedure **derives the order header from the batch**, creates the
   `SOOrders` / `SOOrderDetails` records, and writes the resulting `SOID` back
   onto the staged rows.

Two consequences worth knowing before you build against it:

- **`ImpSalesOrderDetailDto` has ~100 fields.** Line-level (`item`, `qty`,
  `unitPrice`, `warehouseNumber`), header-level (`impCustomerNumber`,
  `poNumber`, `soDate`, `termsCode`, `shipTo*`, `mailTo*`), and pass-through
  (`dealNumber`, `group1..3`, `sfadDealnumber`) are all mixed into one flat
  shape with no required-field markers.
- **Header values must be identical on every line.** The procedure reads them
  off the batch rather than per line, so inconsistent `impCustomerNumber` or
  `shipToAddress` across lines gives you a header built from whichever row wins
  — a silent wrong-data bug, not a validation error.

```python
client.add_sales_order([
    {"impCustomerNumber": "BANKOFAMER", "poNumber": "PO-1001",
     "item": "TONER-BK", "qty": 2, "unitPrice": 89.00},
    {"impCustomerNumber": "BANKOFAMER", "poNumber": "PO-1001",   # repeated
     "item": "DRUM-01",  "qty": 1, "unitPrice": 210.00},
])
```

Once ID634 has created the order, CEO Juice process **ID815** can be configured
to auto-create the linked purchase order.

## Related processes

- **ID285** — has its own namespace, `/api/KM/Id285/*` (`OpenCalls`,
  `CallTypes`, `AddCall`, `Call/{externalRef}`). A separate ticketing flow from
  the main `ServiceCall` routes.
- **ID815** — auto-creates a linked PO after an ID634 sales order.

## Writes have not been exercised

Everything above is confirmed against live reads. The write paths
(`AddCall`, `AddOrder`, `AddMeterReading`, `Customer`/`Contact` create) are
implemented from the spec but **have not been fired**, since even in a sandbox
they mutate a shared dataset. Worth one deliberate round-trip against a
throwaway record before trusting them in a pipeline.
