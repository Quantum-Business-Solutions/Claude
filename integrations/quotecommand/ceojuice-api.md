# CEO Juice / e-automate — API data reference

What QuoteCommand can read out of a dealer's e-automate database through the CEO
Juice Client API, and what it can write back. Measured against the live sandbox on
29 July 2026, not read off the spec — the `Filled` column below is the share of real
sampled records where a field actually carries a value.

> Why that column exists: the spec describes plenty of fields that are null on every
> record. A 0% field is one you cannot build a quote on, and finding that out from a
> table beats finding it out from a customer.

## Connecting

Two steps. Trade a username and password for a JWT, then bearer it on everything else.

```
POST /api/Auth/token   {"username":"…","password":"…"}
  -> {"token":"eyJ…","expires":"2026-07-29T15:18:16Z"}

GET  /api/Customer?pageSize=2
  Authorization: Bearer eyJ…
```

Tokens last about six hours. There is **no OAuth refresh grant** — the only way to
renew is to log in again, which is why `ceojuice_dealer_connections` stores the
password (AES-256-GCM encrypted) rather than a refresh token.

### The `eaapikey` header is not needed

Swagger declares two security schemes — `ApiKey` (an `eaapikey` header) and `Bearer` —
in a single requirement block, which reads as though both are mandatory. They are not.
Bearer alone returns 200; the JWT already carries `ApiKeyId`, so the token *is* the API
key. Verified: `/api/Test` answers 200 with only the bearer header and 401 with none.

## How much data is there

| Object | Records |
| --- | --- |
| Contracts (active) | 1,278 |
| Equipment (active) | 1,109 |
| Sales orders (open) | 635 |
| Service calls (open) | 225 |
| Customers | 160 |
| Contacts | 137 |

Plus populated lookups — 249 models, 59 makes, 70 states, 26 call types, 28 price levels.
The sandbox is the standard e-automate demo dataset and is static; nothing has been
modified since October 2025.

## Average monthly volumes

e-automate computes rolling averages itself, so where they are populated you read them
rather than calculating anything. They arrive per meter, per machine, from
`/api/MeterReadings/EquipmentMetersByEqNo/{eqNo}`:

```
"avgMonthlyVolume3Mo":       0.0
"avgMonthlyVolume6Mo":       0.0
"avgMonthlyVolume12Mo":      0.0
"avgMonthlyVolumeInstall":   0.0
"mfgSuggestedMonthlyVolume": 0.0
"targetMonthlyVolume":       0.0
"meterType": { "meterTypeCode": "B\\W" }
```

**In the sandbox every one of these reads 0.0** — all 34 meters across 41 metered
machines. The demo database never accumulated the reading history the averages derive
from; only 23 of 100 equipment records carry even a most-recent reading.

And there is **no meter-reading-history endpoint**. You can `PUT AddMeterReading` to
write one, and read a single `mostRecentDefaultMeterReadingDisplay` per machine, but
nothing lists readings over time — so where an average is zero it cannot be recomputed
from the raw series, because the series is not exposed.

That matters for quoting: a fleet sized from a volume of zero is wrong in an expensive
direction. `ceojuice-lookup` returns `possiblyUnpopulated: true` when meters exist but
every average is zero, so the UI can say "unknown" instead of "none".

### PrintReleaf is the source that returns real volume today

`/api/PrintReleaf/customers/{id}?startDate&endDate` splits mono from color, and the
window genuinely filters — it reports pages produced inside the range rather than a
lifetime counter:

| Range requested | B/W | Color | Total |
| --- | --- | --- | --- |
| 2024-01-01 → 2024-12-31 | 87,000 | 80,000 | 167,000 |
| 1990-01-01 → 2030-12-31 | 2,493,196 | 439,400 | 2,932,596 |
| 2024-01-01 → 2024-01-31 | *empty array — no data that month* | | |

Divide a 12-month window by 12 and you have a defensible average monthly volume per
customer. Note that a period with no data returns `[]`, which means "no data" and not
"no printing".

## What answers, and what returns 403

49 of 94 documented GET routes answer with a normal dealer key. The refusals track the
claims on the key, and that mapping is published nowhere — a 403 is the only way to
discover it.

**Refused:** the entire `/api/ListsAndCodes/*` family (all 19 routes), `/api/Branch`,
`/api/User/Users`, `/api/User/SalesReps`, `/api/User/Technicians`,
`/api/Process/GetProcessOutput`.

The `ListsAndCodes` block looks like losing every lookup table. It is not — each list
is duplicated under a domain-scoped route gated on the domain claim, and those answer:

| Lookup | Working route |
| --- | --- |
| CallTypes, ProblemCodes, RepairCodes, CancelCodes, OnHoldCodes, Priorities, NoteTypes, SLACodes | `/api/ServiceCall/<name>` |
| States, Countries, Terms, PriceLevels | `/api/Customer/<name>` |
| OrderTypes, OrderStatuses, ShipMethods | `/api/SalesOrder/<name>` |
| MeterTypes | `/api/MeterReadings/MeterTypes` |
| Makes, Models, ModelCategories | `/api/Item/<name>` |

`ceojuice-lookup` takes a list *name* and resolves the route that works, so a caller
cannot reach for the family that 403s.

**The one real gap** is `/api/User/*` and `/api/Branch`. Equipment and service calls
carry `technicianId` and `branchId`, so without those routes you get IDs that cannot be
resolved to names. Worth asking CEO Juice to add those claims.

## Two gotchas that would bite a sync job

**`Recentchanges` caps at 7 days, and exceeding it is not an error.**
`/api/{Entity}/Recentchanges/{sinceTime}` (format `yyyy-MM-ddTHH:mm:ss`) honours a
seven-day window. Ask for 30 days and it returns `{"totalCount":0,"items":[]}` with
HTTP 200 — indistinguishable from "nothing changed". A nightly job that misses a week
would conclude the data is clean and skip every real update. Entities supporting it:
Customer, Contact, Contract, Equipment, Invoice, SalesOrder, ServiceCall.

**Equipment numbers contain spaces.** Real values look like `EQ100023 Dept 330`.
Interpolating one straight into a URL path throws before the request is sent — every
path segment built from dealer data goes through `seg()` in
`_shared/ceojuice-connection.ts`.

## ID136 — service calls

CEO Juice process ID136 is "API sync to ticketing systems". Not an endpoint; it is the
process behind the `ServiceCall` routes — `AddCall`, `AddNote`, `CancelCall` (valid only
before a technician is dispatched), `ByCallNumber`, `AllOpen`, `Recentchanges`.

Either `serialNumber` or `equipmentNumber` is **required** — that is what binds a call
to a machine. Put your own ticket identifier in `referenceCallIdentifier` so calls
reconcile back later.

## ID634 — pushing a quote to a sales order

This is the integration point that matters for QuoteCommand, and it is not a plain
create. `PUT /api/SalesOrder/AddOrder`:

1. Stages **one row per order line** into `ZCJ_ImpSOOrderDetails`, all sharing a
   generated `SourceID`.
2. Invokes stored procedure `ZCJ_Event_634_Log` with that `SourceID`.
3. That procedure **derives the header from the batch**, creates the `SOOrders` /
   `SOOrderDetails` records, and writes the resulting `SOID` back onto the staged rows.

CEO Juice's own description: it validates each row against existing customer, branch,
item, warehouse and sales-rep records, and **holds** invalid orders rather than skipping
them.

Three things follow, and `ceojuice-push-order` is built around them:

**Header fields must be identical on every line.** The procedure reads them off the
batch, not per line. Inconsistent values raise no validation error — the header is built
from whichever row wins, which is silent wrong data. `normaliseHeader` stamps one header
onto every line and reports which fields it had to override.

**A 200 does not mean an order exists.** It means the batch was accepted for import; the
order may be held awaiting correction. The function deliberately does not report "order
created" on a 200.

**Retrying is dangerous.** Because the outcome is ambiguous, the reflex is to push
again, and that is how one quote becomes two orders. A partial unique index on
`ceojuice_order_pushes (quote_id) WHERE status = 'succeeded'` makes the second attempt
fail at the database.

The DTO carries explicit quote linkage — `quoteNumber`, `quoteID`, `quoteDetailID`,
`dealNumber`, `sfadDealnumber` — so the quote reference survives into e-automate and the
two records can be reconciled afterwards.

Related: process **ID815** can be configured to auto-create the linked purchase order
once ID634 has created the sales order.

## Where to see the records yourself

| Where | What it shows |
| --- | --- |
| `devclientsapi.ceojuice.com/swagger/index.html` | The records. Click **Authorize**, paste a JWT from `/api/Auth/token`, then *Try it out* on any endpoint. |
| `www.ceojuice.com` → `/Identity/Account/Login` | Alert and process **configuration** — subscriptions, surveys, profile. Login is your email; the password was emailed. **Not** a record browser. |
| e-automate itself / CEO Juice SSRS reports | Record-level reporting. Ask CEO Juice for access; raw `ZCJ_*` table access needs the e-automate database. |

> The production API hostname is **unknown**. `clientsapi.ceojuice.com` does not resolve,
> so only the dev host is confirmed. Ask CEO Juice for the production URL before going
> live — `base_url` is per dealer and deliberately not defaulted for this reason.

## Field reference

887 fields across 31 objects.

### Objects you read

### Customer

53 fields · `/api/Customer` · sampled 160 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `customerId` | int | 100% | `1` |
| `billtoId` | int | 100% | `1` |
| `locationId` | int | 100% | `1` |
| `customerNumber` | string | 100% | `BANKOFAMER` |
| `customerName` | string | 100% | `Bank of America` |
| `attn` | string | 38% | `Lisa Beal` |
| `address` | string | 92% | `14511 Falling Creek #103` |
| `city` | string | 92% | `Houston` |
| `state` | string | 89% | `TX` |
| `zip` | string | 86% | `77014` |
| `country` | string | 8% | `USA` |
| `county` | string | 11% | `Montgomery` |
| `longitude` | decimal | 0% |  |
| `latitude` | decimal | 0% |  |
| `phone1` | string | 82% | `(281) 397-4325` |
| `phone2` | string | 71% | `713-234-8765` |
| `fax` | string | 75% | `713-292-7654` |
| `email` | string | 22% | `sample@customer.com` |
| `webSite` | string | 31% | `www.bankofamerica.com` |
| `prospect` | boolean | 100% | `False` |
| `salesRepId` | int | 81% | `2` |
| `priceLevelId` | int | 100% | `2` |
| `customerTypeId` | int | 86% | `1` |
| `blanketPO` | string | 8% | `54321` |
| `hold` | boolean | 100% | `True` |
| `remarks` | string | 13% | `Notes for Bank of America main loc` |
| `active` | boolean | 100% | `True` |
| `shipTo` | boolean | 100% | `False` |
| `branchId` | int | 100% | `1` |
| `lastUpdate` | datetime | 100% | `2025-10-22T11:13:27.947` |
| `technicianId` | int | 71% | `1` |
| `territoryId` | int | 70% | `2` |
| `companyCustomer` | boolean | 100% | `False` |
| `requirePONum` | boolean | 100% | `True` |
| `allowAutoMeterRequests` | boolean | 100% | `False` |
| `taxable` | boolean | 100% | `True` |
| `onHoldCodeId` | int | 3% | `1` |
| `timeZoneCodeID` | int | 42% | `9` |
| `billToAttn` | string | 0% |  |
| `billToAddress` | string | 1% | `P.O. Box 686` |
| `billToCity` | string | 1% | `Dubai` |
| `billToCounty` | string | 1% | `United Arab Emirates` |
| `billToState` | string | 0% |  |
| `billToZip` | string | 0% |  |
| `billToCountry` | string | 0% |  |
| `mapAddress` | string | 0% |  |
| `mapCity` | string | 0% |  |
| `mapState` | string | 0% |  |
| `mapZip` | string | 0% |  |
| `mapCountry` | string | 0% |  |
| `miles` | decimal | 100% | `0.0` |
| `noteCount` | int | 100% | `1` |
| `slaCodeId` | int | 17% | `4` |

### Contact

26 fields · `/api/Contact` · sampled 137 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `contactId` | int | 100% | `1` |
| `contactNumber` | string | 0% |  |
| `lastName` | string | 0% |  |
| `firstName` | string | 0% |  |
| `middleName` | string | 0% |  |
| `prefName` | string | 0% |  |
| `prefFullName` | string | 0% |  |
| `address` | string | 0% |  |
| `city` | string | 0% |  |
| `state` | string | 0% |  |
| `zip` | string | 0% |  |
| `country` | string | 0% |  |
| `phone1` | string | 0% |  |
| `phone2` | string | 0% |  |
| `fax` | string | 0% |  |
| `email` | string | 0% |  |
| `allEmails` | string | 0% |  |
| `remarks` | string | 0% |  |
| `active` | boolean | 0% |  |
| `attn` | string | 0% |  |
| `salesRepId` | int | 0% |  |
| `preferedContactMethodId` | int | 0% |  |
| `emailType` | boolean | 0% |  |
| `sendShippingConfirmations` | boolean | 0% |  |
| `noteCount` | int | 0% |  |
| `lastUpdate` | datetime | 0% |  |

### Equipment

68 fields · `/api/Equipment/AllActive` · sampled 200 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `equipmentId` | int | 100% | `1` |
| `equipmentNumber` | string | 100% | `12345` |
| `itemId` | int | 100% | `4` |
| `serialNumber` | string | 96% | `27V02385` |
| `customerId` | int | 100% | `1` |
| `billtoId` | int | 100% | `2` |
| `locationId` | int | 98% | `1` |
| `address` | string | 98% | `14511 Falling Creek #103` |
| `city` | string | 100% | `Houston` |
| `state` | string | 100% | `TX` |
| `zip` | string | 100% | `77014` |
| `country` | string | 32% | `USA` |
| `locationDescription` | string | 12% | `Copy room on 4th floor` |
| `officeOpen` | datetime | 14% | `2025-10-16T08:00:00` |
| `officeClose` | datetime | 14% | `2025-10-16T17:00:00` |
| `installDate` | datetime | 12% | `2000-01-01T00:00:00` |
| `contact` | string | 18% | `Mark Watthuber` |
| `contactPhone` | string | 12% | `915-421-9876` |
| `contactFax` | string | 7% | `915-421-9426` |
| `decisionMaker` | string | 14% | `Jim Smith` |
| `decisionMakerPhone` | string | 13% | `480-569-4899` |
| `decisionMakerFax` | string | 5% | `847-549-1545` |
| `territoryId` | int | 100% | `2` |
| `technicianId` | int | 100% | `2` |
| `warrantyDate` | datetime | 12% | `2000-04-20T00:00:00` |
| `warrantyMeter` | int | 54% | `50000` |
| `pmMeterInterval` | int | 53% | `10000` |
| `pmMeterDue` | int | 53% | `70000` |
| `pmDateInterval` | int | 8% | `180` |
| `pmDateDue` | datetime | 8% | `2005-07-10T00:00:00` |
| `pmUseMeter` | boolean | 100% | `True` |
| `pmUseDate` | boolean | 100% | `True` |
| `remarks` | string | 4% | `Notes for this specific machine ca` |
| `active` | boolean | 100% | `True` |
| `lastUpdate` | datetime | 100% | `2025-10-16T16:49:38.577` |
| `statusId` | int | 57% | `1002` |
| `conditionId` | int | 22% | `3` |
| `branchId` | int | 100% | `1` |
| `parentId` | int | 1% | `22` |
| `hosting` | boolean | 100% | `True` |
| `attached` | boolean | 100% | `False` |
| `leaseId` | int | 4% | `2` |
| `leaseEquipmentNumber` | string | 0% |  |
| `modelId` | int | 100% | `1` |
| `isMetered` | boolean | 100% | `True` |
| `requireMeteronServiceCalls` | boolean | 100% | `False` |
| `mostRecentDefaultMeterReadingDisplay` | decimal | 16% | `87000.0` |
| `mostRecentDefaultMeterReadingDate` | datetime | 16% | `2024-12-12T00:00:00` |
| `priorityId` | int | 12% | `1` |
| `equipmentContactId` | int | 10% | `1` |
| `decisionContactId` | int | 10% | `4` |
| `allowAutoMeterRequests` | boolean | 100% | `False` |
| `nextMeterReading` | datetime | 0% |  |
| `lastMeterRequest` | datetime | 0% | `2008-02-05T11:06:48.857` |
| `timeZoneCodeId` | int | 0% |  |
| `expireByUsage` | boolean | 100% | `False` |
| `warrantyEndMeter` | decimal | 0% |  |
| `meterContactId` | int | 10% | `1` |
| `assetId` | int | 0% |  |
| `ipAddress` | string | 0% |  |
| `macAddress` | string | 0% |  |
| `noteCount` | int | 100% | `0` |
| `slaCodeId` | int | 100% | `2` |
| `model` | Model | 0% |  |
| `customer` | Customer | 0% |  |
| `location` | Customer | 0% |  |
| `billTo` | Customer | 0% |  |
| `slaCode` | SLACode | 0% |  |

### ServiceCall

24 fields · `/api/ServiceCall/AllOpen` · sampled 200 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `callId` | int | 100% | `1043` |
| `callNumber` | string | 100% | `1140` |
| `customerId` | int | 100% | `32` |
| `status` | string | 100% | `P` |
| `description` | string | 92% | `Note here` |
| `notes` | string | 62% | `test` |
| `date` | datetime | 100% | `2018-02-05T14:55:00` |
| `reqDate` | datetime | 100% | `2018-02-05T14:55:00` |
| `estStartDate` | datetime | 100% | `2019-03-11T12:00:00` |
| `closeDate` | datetime | 0% | `2024-07-18T11:32:00` |
| `creatorId` | string | 100% | `Mark` |
| `createDate` | datetime | 100% | `2011-08-09T14:56:55.577` |
| `updatorId` | string | 100% | `Mark` |
| `lastUpdate` | datetime | 100% | `2019-03-11T13:35:42.743` |
| `equipment` | Equipment | 0% |  |
| `technician` | Agent | 0% |  |
| `addressStreet` | string | 100% | `1430-K Village Way` |
| `addressCity` | string | 100% | `Santa Ana` |
| `addressState` | string | 100% | `CA` |
| `addressZip` | string | 100% | `92705` |
| `addressCountry` | string | 6% | `USA` |
| `caller` | string | 98% | `714-547-9500` |
| `trackingKey` | string | 0% |  |
| `externalId` | string | 0% |  |

### SalesOrder

77 fields · `/api/SalesOrder/AllOpen` · sampled 200 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `soId` | int | 100% | `8` |
| `soNumber` | string | 100% | `108` |
| `customerId` | int | 100% | `5` |
| `billToId` | int | 100% | `5` |
| `locationId` | int | 84% | `16` |
| `date` | datetime | 100% | `2000-03-29T00:00:00` |
| `description` | string | 12% | `HP 3150 Printer` |
| `poNumber` | string | 46% | `1234` |
| `reqDate` | datetime | 100% | `2000-04-28T00:00:00` |
| `termId` | int | 99% | `1` |
| `termDiscountRate` | decimal | 100% | `0` |
| `termDiscountDate` | datetime | 5% | `2008-04-16T00:00:00` |
| `dueDate` | datetime | 100% | `2000-04-28T00:00:00` |
| `shipMethodId` | int | 100% | `3` |
| `jobId` | int | 1% | `1` |
| `salesRepId` | int | 97% | `1` |
| `mailToAttn` | string | 45% | `Mike Dixon` |
| `mailToName` | string | 100% | `Wells Fargo Bank` |
| `mailToAddress` | string | 98% | `89 Main Street` |
| `mailToCity` | string | 98% | `The Woodlands` |
| `mailToState` | string | 98% | `TX` |
| `mailToZip` | string | 98% | `77381` |
| `mailToCountry` | string | 30% | `USA` |
| `shipToName` | string | 100% | `Wells Fargo Bank` |
| `shipToAttn` | string | 49% | `Susan Jenson` |
| `shipToAddress` | string | 94% | `89 Main Street` |
| `shipToCity` | string | 94% | `The Woodlands` |
| `shipToState` | string | 94% | `TX` |
| `shipToZip` | string | 94% | `77381` |
| `shipToCountry` | string | 28% | `USA` |
| `remarks` | string | 4% | `Notes....` |
| `discountRate` | decimal | 100% | `0.0` |
| `discount` | decimal | 100% | `0.0` |
| `freight` | decimal | 100% | `0.0` |
| `taxCodeId` | int | 94% | `10` |
| `tax` | decimal | 100% | `14.5` |
| `total` | decimal | 100% | `214.5` |
| `approvedById` | int | 4% | `1` |
| `onHold` | boolean | 100% | `False` |
| `onHoldCodeId` | int | 18% | `1` |
| `onHoldReleaseDate` | datetime | 11% | `2003-03-05T09:19:55` |
| `onHoldReleaserId` | string | 11% | `Admin` |
| `branchId` | int | 100% | `1` |
| `chargeMethodId` | int | 19% | `3` |
| `taxable` | boolean | 100% | `True` |
| `amountTotal` | decimal | 100% | `200.0` |
| `amountPicketed` | decimal | 100% | `200.0` |
| `amountShipped` | decimal | 100% | `0.0` |
| `amountFulFilled` | decimal | 100% | `0.0` |
| `amountBilled` | decimal | 100% | `0.0` |
| `quantityTotal` | decimal | 100% | `1.0` |
| `quantityShipped` | decimal | 100% | `0.0` |
| `quantityFulfilled` | decimal | 100% | `0.0` |
| `quantityBilled` | decimal | 100% | `0.0` |
| `billedFreight` | decimal | 100% | `0.0` |
| `orderTypeId` | int | 100% | `2` |
| `warehouseId` | int | 30% | `1` |
| `amountBackOrdered` | decimal | 100% | `0.0` |
| `quantityBackOrdered` | decimal | 100% | `0.0` |
| `statusId` | int | 100% | `1` |
| `returnCodeId` | int | 2% | `3` |
| `origInvoiceId` | int | 0% | `177` |
| `returnMethodId` | int | 2% | `3` |
| `orderedByContactId` | int | 2% | `31` |
| `quoteId` | int | 4% | `90` |
| `quoteOriginatorEmail` | string | 4% | `mwatthuber@sbcglobal.net` |
| `noteCount` | int | 100% | `0` |
| `sendShippingNotifications` | boolean | 100% | `False` |
| `sendShippingNotificationToOrderByContact` | boolean | 100% | `False` |
| `shippingNotificationAdditionalEmails` | string | 0% |  |
| `taxExemptCodeId` | int | 0% |  |
| `salesRep` | Agent | 0% |  |
| `customer` | Customer | 0% |  |
| `billTo` | Customer | 0% |  |
| `orderType` | SOOrderType | 0% |  |
| `status` | SoStatus | 0% |  |
| `details` | SOOrderDetail[] | 100% | `<list>` |

### Contract

117 fields · `/api/Contract/active` · sampled 200 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `contractId` | int | 100% | `8` |
| `contractNumber` | string | 100% | `109-01` |
| `contractMajor` | string | 100% | `109` |
| `contractMinor` | string | 100% | `01` |
| `customerId` | int | 100% | `2` |
| `contact` | string | 61% | `Judy Smith` |
| `phone` | string | 52% | `936-271-9034` |
| `fax` | string | 47% | `936-271-9001` |
| `billToId` | int | 100% | `2` |
| `contractCodeId` | int | 100% | `4` |
| `billCodeId` | int | 100% | `7` |
| `billGroupId` | int | 5% | `4` |
| `startdate` | datetime | 100% | `2001-03-01T00:00:00` |
| `expDate` | datetime | 100% | `2002-03-01T00:00:00` |
| `expCopies` | int | 2% | `10000` |
| `baseNextBillingDate` | datetime | 84% | `2005-09-09T00:00:00` |
| `baseLastBillingDate` | datetime | 84% | `2004-09-09T00:00:00` |
| `baseBillingCycleId` | int | 84% | `2` |
| `baseArrears` | boolean | 100% | `False` |
| `sumIndividualBaseRates` | boolean | 100% | `False` |
| `baseRate` | decimal | 100% | `0.0` |
| `baseRatePeriod` | int | 100% | `12` |
| `overageNextBillingDate` | datetime | 69% | `2005-03-19T00:00:00` |
| `overageLastBillingDate` | datetime | 83% | `2001-03-01T00:00:00` |
| `overageBillingCycleId` | int | 28% | `1` |
| `bsaBillForServices` | boolean | 100% | `True` |
| `bsaLaborDiscount` | decimal | 2% | `0` |
| `bsaMaterialsDiscount` | decimal | 2% | `0` |
| `bsaMinimumBalance` | decimal | 100% | `500.0` |
| `bsaMinimumBilling` | decimal | 100% | `1000.0` |
| `coveredCopies` | int | 0% |  |
| `groupInvoices` | boolean | 100% | `False` |
| `poNumber` | string | 28% | `54321` |
| `miscChargeAmount` | decimal | 100% | `0.0` |
| `miscChargeTaxFlag` | int | 100% | `0` |
| `miscChargeDescription` | string | 11% | `"24-7"` |
| `miscContinuous` | boolean | 100% | `False` |
| `remarks` | string | 2% | `Notes for contract 131-02 go here` |
| `unearnedBalance` | decimal | 100% | `796.11` |
| `bill` | boolean | 100% | `True` |
| `activated` | datetime | 100% | `2001-03-01T15:13:30` |
| `terminated` | datetime | 0% |  |
| `renewed` | datetime | 100% | `2007-01-22T00:00:00` |
| `active` | boolean | 100% | `True` |
| `lastUpdate` | datetime | 100% | `2007-01-22T15:08:19.107` |
| `leaseSchedule` | string | 4% | `12-345678` |
| `taxCodeId` | int | 99% | `7` |
| `branchId` | int | 100% | `1` |
| `contractLeaseId` | int | 2% | `14` |
| `useLeaseOnAllEquipment` | boolean | 100% | `False` |
| `remarksInternal` | string | 2% | `note here` |
| `termId` | int | 100% | `3` |
| `salesRepId` | int | 94% | `10` |
| `jobId` | int | 2% | `2` |
| `accumCopies` | decimal | 0% |  |
| `expCopyExpDate` | datetime | 0% |  |
| `contactId` | int | 47% | `14` |
| `billToAttn` | string | 48% | `Sharon Masters` |
| `billToAddress` | string | 98% | `415 North Frazier` |
| `billToCity` | string | 98% | `Conroe` |
| `billToState` | string | 96% | `TX` |
| `billToZip` | string | 96% | `77301` |
| `billToCountry` | string | 14% | `USA` |
| `baseBilledThruDate` | datetime | 80% | `2004-09-08T00:00:00` |
| `overageBilledThruDate` | datetime | 35% | `2005-02-18T00:00:00` |
| `baseAccruedThruDate` | datetime | 66% | `2004-09-08T00:00:00` |
| `renewable` | boolean | 100% | `True` |
| `baseRateScheduleStartDate` | datetime | 78% | `2002-06-19T00:00:00` |
| `ovgRateScheduleStartDate` | datetime | 78% | `2002-06-19T00:00:00` |
| `renewalCycleId` | int | 27% | `1` |
| `nextBaseIncreaseDate` | datetime | 1% | `2013-07-01T00:00:00` |
| `nextOvgIncreaseDate` | datetime | 0% |  |
| `taxable` | boolean | 100% | `False` |
| `baseBillingStartDate` | datetime | 75% | `2005-07-13T00:00:00` |
| `overageBillingStartDate` | datetime | 22% | `2004-05-20T00:00:00` |
| `useAlternateOvgBillTo` | boolean | 100% | `False` |
| `ovgBillToId` | int | 1% | `62` |
| `ovgBillToAttn` | string | 0% |  |
| `ovgBillToAddress` | string | 0% |  |
| `ovgBillToCity` | string | 0% |  |
| `ovgBillToState` | string | 0% |  |
| `ovgBillToZip` | string | 0% |  |
| `ovgBillToCountry` | string | 0% |  |
| `ovgBillToTermId` | int | 0% |  |
| `contractAdjCodeId` | int | 25% | `2` |
| `useIndividualTaxCodes` | boolean | 100% | `False` |
| `terminationCodeId` | int | 0% |  |
| `contractStatusId` | int | 100% | `6` |
| `oneTimeRemark` | string | 1% | `Notes 11111111111111111111111` |
| `printOneTimeRemark` | boolean | 100% | `False` |
| `ovgBillToTaxable` | boolean | 100% | `False` |
| `ovgBillToTaxCodeId` | int | 50% | `7` |
| `ovgBillToUseIndividualTaxCodes` | boolean | 100% | `False` |
| `allowMeterEstimation` | boolean | 100% | `True` |
| `expCopiesBase` | int | 100% | `0` |
| `expAdjCopies` | int | 100% | `0` |
| `expCopiesActualExpDate` | datetime | 2% | `2009-02-01T00:00:00` |
| `expDateInitial` | datetime | 99% | `2002-03-01T00:00:00` |
| `cppMinimumPages` | int | 100% | `0` |
| `cppRate` | decimal | 100% | `0.0` |
| `cppHardwareAmount` | decimal | 100% | `0.0` |
| `cppServiceRate` | decimal | 100% | `0.0` |
| `combineLeaseAndBase` | boolean | 100% | `False` |
| `timeBlockBased` | boolean | 100% | `False` |
| `noteCount` | int | 100% | `0` |
| `baseRatePeriodType` | int | 100% | `1` |
| `unearnedInterestBalance` | decimal | 100% | `0.0` |
| `unearnedLeaseBalance` | decimal | 100% | `0.0` |
| `unearnedLeasePostTermBalance` | decimal | 100% | `0.0` |
| `message` | string | 0% |  |
| `messReqAcknowledgment` | boolean | 100% | `True` |
| `taxExemptCodeId` | int | 0% |  |
| `ovgBillToTaxExemptCodeId` | int | 0% |  |
| `slaCodeId` | int | 6% | `4` |
| `customer` | Customer | 0% |  |
| `billTo` | Customer | 0% |  |
| `details` | ContractDetail[] | 100% | `<list>` |

### Invoice

77 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `invoiceId` | int |
| `invoiceNumber` | string |
| `type` | string |
| `customerId` | int |
| `billToId` | int |
| `applyToId` | int |
| `masterInvoiceId` | int |
| `locationId` | int |
| `date` | datetime |
| `datePeriod` | int |
| `period` | int |
| `description` | string |
| `poNumber` | string |
| `termId` | int |
| `termDiscountRate` | decimal |
| `termDiscountDate` | datetime |
| `termDiscount` | decimal |
| `dueDate` | datetime |
| `salesRepId` | int |
| `mailToAttn` | string |
| `mailToName` | string |
| `mailToAddress` | string |
| `mailToCity` | string |
| `mailToState` | string |
| `mailToZip` | string |
| `mailToCountry` | string |
| `shipToAttn` | string |
| `shipToName` | string |
| `shipToAddress` | string |
| `shipToCity` | string |
| `shipToState` | string |
| `shipToZip` | string |
| `shipToCountry` | string |
| `remarks` | string |
| `discountRate` | decimal |
| `discount` | decimal |
| `freight` | decimal |
| `taxCodeId` | int |
| `tax` | decimal |
| `total` | decimal |
| `adjTotal` | decimal |
| `due` | decimal |
| `voidId` | int |
| `module` | string |
| `source` | string |
| `reference` | string |
| `creatorId` | string |
| `updatorId` | string |
| `createDate` | datetime |
| `lastUpdate` | datetime |
| `transactionTypeId` | int |
| `chargeMethodId` | int |
| `chargeAccountInfo` | string |
| `taxable` | boolean |
| `freightDeptId` | int |
| `discountDeptId` | int |
| `consolidate` | boolean |
| `consolidatedBillingId` | int |
| `billingNumber` | string |
| `isVoid` | boolean |
| `sent` | boolean |
| `noteId` | int |
| `noteFlag` | int |
| `orderedByContactId` | int |
| `sendContactId` | int |
| `sendMethodId` | int |
| `receivablePayableId` | int |
| `primaryReportDefinitionId` | int |
| `noteCount` | int |
| `extReferenceNumber` | string |
| `commissionRepId` | int |
| `taxExemptCodeId` | int |
| `freightTaxFlag` | int |
| `freightTaxFlagId` | int |
| `customer` | Customer |
| `billTo` | Customer |
| `details` | InvoiceDetail[] |

### ContractDetail

67 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `contractDetailId` | int |
| `contractId` | int |
| `equipmentId` | int |
| `locationId` | int |
| `baseRate` | decimal |
| `billCodeId` | int |
| `useContractLease` | boolean |
| `startDate` | datetime |
| `endDate` | datetime |
| `baseBilledThruDate` | datetime |
| `overageBilledThruDate` | datetime |
| `baseAccruedThruDate` | datetime |
| `prorateStart` | boolean |
| `prorateStartAmount` | decimal |
| `prorateStartBillNow` | boolean |
| `prorateEnd` | boolean |
| `prorateEndAmount` | decimal |
| `prorateEndBillNow` | boolean |
| `address` | string |
| `city` | string |
| `state` | string |
| `zip` | string |
| `country` | string |
| `nextBaseIncreaseDate` | datetime |
| `unEarnedBalance` | decimal |
| `prorateStartAutoCalc` | boolean |
| `prorateEndAutoCalc` | boolean |
| `startMeterReadingDate` | datetime |
| `endMeterReadingDate` | datetime |
| `baseRateScheduleStartDate` | datetime |
| `taxCodeId` | int |
| `terminationCodeId` | int |
| `quantity` | decimal |
| `unitBaseRate` | decimal |
| `noteCount` | int |
| `billStartDate` | datetime |
| `billEndDate` | datetime |
| `parentContractDetailId` | int |
| `contractDetailTypeId` | int |
| `subLeaseNumber` | string |
| `subLeaseMajor` | string |
| `subLeaseMinor` | string |
| `leaseTerm` | int |
| `leasePaymentStartDate` | datetime |
| `leasePaymentEndDate` | datetime |
| `leaseRate` | decimal |
| `leaseRateFactor` | decimal |
| `leaseInterestRate` | decimal |
| `leaseFinancedAmount` | decimal |
| `leasePaymentAmount` | decimal |
| `leasePrincipalBalance` | decimal |
| `combineWithParentBaseAmount` | boolean |
| `unearnedInterestBalance` | decimal |
| `unearnedLeaseBalance` | decimal |
| `unearnedLeasePostTermBalance` | decimal |
| `leaseTerminationCodeId` | int |
| `assetNumber` | string |
| `taxExemptCodeId` | int |
| `taxable` | boolean |
| `overrideTaxable` | boolean |
| `itemId` | int |
| `description` | string |
| `locationRemarks` | string |
| `slaCodeId` | int |
| `equipment` | Equipment |
| `location` | Customer |
| `slaCode` | SLACode |

### SOOrderDetail

38 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `soId` | int |
| `detailId` | int |
| `itemId` | int |
| `description` | string |
| `quantity` | decimal |
| `um` | string |
| `price` | decimal |
| `equipmentId` | int |
| `contractId` | int |
| `bill` | boolean |
| `discount` | decimal |
| `stocked` | boolean |
| `amount` | decimal |
| `backOrdered` | decimal |
| `picketed` | decimal |
| `shipped` | decimal |
| `canceled` | decimal |
| `billed` | decimal |
| `workOrderId` | int |
| `returnCodeId` | int |
| `returnRemarks` | string |
| `fulfilled` | decimal |
| `remarks` | string |
| `isReturn` | boolean |
| `isRMAReturn` | boolean |
| `trackingNumber` | string |
| `earliestDate` | datetime |
| `latestDate` | datetime |
| `notes` | string |
| `shipToContactId` | int |
| `lineNumber` | string |
| `displayPrice` | decimal |
| `displayAmount` | decimal |
| `displayDiscount` | decimal |
| `contractDetailId` | int |
| `branchId` | int |
| `item` | Item |
| `equipment` | Equipment |

### InvoiceDetail

15 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `invoiceId` | int |
| `detailId` | int |
| `description` | string |
| `amount` | decimal |
| `taxFlag` | int |
| `cost` | decimal |
| `creatorId` | string |
| `updatorId` | string |
| `createDate` | datetime |
| `lastUpdate` | datetime |
| `taxCodeId` | int |
| `lineNumber` | string |
| `taxable` | boolean |
| `taxExemptCodeId` | int |
| `taxFlagId` | int |

### ModelMeters

23 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `modelMeterId` | int |
| `modelId` | int |
| `meterTypeId` | int |
| `description` | string |
| `meterDigits` | int |
| `requireReading` | boolean |
| `warrantyClicks` | decimal |
| `doPMByClicks` | boolean |
| `pmIntervalClicks` | decimal |
| `pmDueClicks` | decimal |
| `meterFormula` | string |
| `isDefault` | boolean |
| `interfaceName` | string |
| `active` | boolean |
| `avgMonthlyVolume3Mo` | decimal |
| `avgMonthlyVolume6Mo` | decimal |
| `avgMonthlyVolume12Mo` | decimal |
| `avgMonthlyVolumeInstall` | decimal |
| `mfgSuggestedMonthlyVolume` | decimal |
| `targetMonthlyVolume` | decimal |
| `includeInMeterRequests` | boolean |
| `sequentialMeter` | boolean |
| `meterType` | MeterType |

### PrintReleafUsageRecord

9 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `customerId` | int |
| `customerNumber` | string |
| `customerName` | string |
| `periodStart` | datetime |
| `periodEnd` | datetime |
| `blackAndWhitePages` | int |
| `colorPages` | int |
| `duplexCount` | int |
| `totalPages` | int |

### Item

10 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `itemId` | int |
| `itemNumber` | string |
| `description` | string |
| `onHandQty` | decimal |
| `active` | boolean |
| `prefMfgNumber` | string |
| `modelId` | int |
| `model` | Model |
| `defaultPrice` | decimal |
| `customerPrice` | decimal |

### Payloads you write

### NewServiceCallDto

13 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `description` | string |
| `callDate` | datetime |
| `serialNumber` | string |
| `equipmentNumber` | string |
| `customerNumber` | string |
| `referenceCallIdentifier` | string |
| `contact` | string |
| `contactName` | string |
| `contactPhone` | string |
| `contactEmail` | string |
| `notes` | string |
| `callType` | string |
| `trackingKey` | string |

### ImpSalesOrderDetailDto

103 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `impSONumber` | string |
| `impInvNumber` | string |
| `description` | string |
| `impCustomerNumber` | string |
| `impShipToCustomerNumber` | string |
| `impBillToCustomerNumber` | string |
| `soDate` | datetime |
| `salesRepNumber` | string |
| `branchNumber` | string |
| `poNumber` | string |
| `item` | string |
| `detailDesc` | string |
| `qty` | decimal |
| `unitPrice` | decimal |
| `lineExtTotal` | decimal |
| `glAcctNumber` | string |
| `glDeptNumber` | string |
| `taxFlag` | string |
| `batch` | string |
| `detailID` | int |
| `equipmentNumber` | string |
| `contractNumber` | string |
| `remarks` | string |
| `notes` | string |
| `warehouseNumber` | string |
| `binNumber` | string |
| `outCost` | decimal |
| `parentID` | int |
| `soNumber` | string |
| `quoteNumber` | string |
| `quoteID` | int |
| `quoteDetailID` | int |
| `mailtoAttn` | string |
| `mailToName` | string |
| `mailToAddress` | string |
| `mailToCity` | string |
| `mailToState` | string |
| `mailToZip` | string |
| `mailToCountry` | string |
| `shipToAttn` | string |
| `shipToName` | string |
| `shipToAddress` | string |
| `shipToCity` | string |
| `shipToState` | string |
| `shipToZip` | string |
| `shipToCountry` | string |
| `onHoldCode` | string |
| `orderType` | string |
| `shipToTypeID` | int |
| `contactNumber` | string |
| `reqDate` | datetime |
| `shipMethod` | string |
| `itemTemplate` | string |
| `vendor` | string |
| `vendorItem` | string |
| `vendorCost` | decimal |
| `vendorExternalLinkedPO` | string |
| `uom` | string |
| `defaultPrice` | decimal |
| `vendorNumber` | string |
| `detailParentID` | int |
| `priceBookName` | string |
| `isDevice` | boolean |
| `shipToContactNumber` | string |
| `orgSONumber` | string |
| `targEAOrderStatus` | string |
| `deliveryRemarks` | string |
| `jobNumber` | string |
| `hiddenLine` | int |
| `rollUpPrice` | int |
| `configParentShipID` | string |
| `lineNumber` | string |
| `sortOrder` | int |
| `depth` | int |
| `taxCode` | string |
| `termsCode` | string |
| `approver` | string |
| `message` | string |
| `orderBreak` | string |
| `freight` | decimal |
| `dealNumber` | string |
| `altSalesRepNumber` | string |
| `altSalesRepNumber2` | string |
| `altSalesRepNumber3` | string |
| `isLease` | boolean |
| `orderedByEmail` | string |
| `orderedByFirstName` | string |
| `orderedByLastName` | string |
| `orderedByPhone` | string |
| `group1` | string |
| `group2` | string |
| `group3` | string |
| `qtyBackOrder` | decimal |
| `soBranchNumber` | string |
| `sfadDealnumber` | string |
| `impDiscount` | decimal |
| `impDiscountPrct` | decimal |
| `salesCategory` | string |
| `impDetailID` | int |
| `targEAOrderDetailStatus` | string |
| `hideOnPackingList` | boolean |
| `hideOnPickingList` | boolean |
| `soWarehouseNumber` | string |

### CreateCustomerRequest

31 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `customerName` | string |
| `attn` | string |
| `address` | string |
| `city` | string |
| `state` | string |
| `zip` | string |
| `country` | string |
| `phone1` | string |
| `phone2` | string |
| `fax` | string |
| `email` | string |
| `website` | string |
| `ein` | string |
| `taxNumber` | string |
| `taxCodeId` | int |
| `blanketPO` | string |
| `remarks` | string |
| `branchId` | int |
| `parentCustomerId` | int |
| `billToCustomerId` | int |
| `priceLevelId` | int |
| `termId` | int |
| `shipMethodId` | int |
| `creditLimit` | decimal |
| `doFinCharges` | boolean |
| `prospect` | boolean |
| `hold` | boolean |
| `onHoldCodeId` | int |
| `salesRepId` | int |
| `county` | string |
| `customerNumber` | string |

### CreateContactRequest

20 fields · *shape from spec only — no list route to sample*

| Field | Type |
| --- | --- |
| `lastName` | string |
| `firstName` | string |
| `middleName` | string |
| `prefName` | string |
| `prefFullName` | string |
| `address` | string |
| `city` | string |
| `state` | string |
| `zip` | string |
| `country` | string |
| `phone1` | string |
| `phone2` | string |
| `fax` | string |
| `email` | string |
| `remarks` | string |
| `salesRepId` | int |
| `active` | boolean |
| `preferredContactMethodId` | int |
| `emailType` | boolean |
| `customerNumber` | string |

### Lookup tables

### Make

15 fields · `/api/Item/Makes` · sampled 59 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `makeID` | int | 100% | `50` |
| `name` | string | 100% | `Altronic` |
| `description` | string | 100% | `Altronic` |
| `remarks` | string | 2% | `This is a generic make for all new` |
| `active` | boolean | 100% | `True` |
| `locks` | int | 100% | `0` |
| `creatorID` | string | 100% | `Mark` |
| `updatorID` | string | 100% | `Mark` |
| `createDate` | datetime | 100% | `2016-06-02T13:50:43.897` |
| `lastUpdate` | datetime | 100% | `2016-06-02T13:50:43.897` |
| `timestamp` | string | 100% | `AAAAAACBupw=` |
| `shTrackingConfigID` | int | 14% | `18` |
| `noteID` | int | 2% | `1` |
| `noteFlag` | int | 100% | `0` |
| `noteCount` | int | 100% | `0` |

### Model

8 fields · `/api/Item/Models` · sampled 200 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `modelID` | int | 100% | `2` |
| `name` | string | 100% | `"Model Number Here"` |
| `description` | string | 100% | `"Model Description Here"` |
| `active` | boolean | 100% | `True` |
| `make` | Make | 100% | `<dict>` |
| `modelCategory` | ModelCategory | 100% | `<dict>` |
| `priorityId` | int | 59% | `1` |
| `meters` | ModelMeters[] | 100% | `<list>` |

### CallType

10 fields · `/api/ServiceCall/CallTypes` · sampled 26 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `callTypeID` | int | 100% | `5` |
| `callTypeCode` | string | 100% | `CS` |
| `description` | string | 100% | `Carrier Stuck` |
| `estDuration` | int | 100% | `60` |
| `category` | string | 100% | `CM` |
| `priorityID` | int | 100% | `3` |
| `active` | boolean | 100% | `True` |
| `icon` | string | 88% | `CirBlue` |
| `escalate` | boolean | 96% | `False` |
| `activityCodeId` | int | 100% | `3` |

### State

5 fields · `/api/Customer/States` · sampled 70 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `stateId` | int | 100% | `58` |
| `code` | string | 100% | `AB` |
| `stateName` | string | 100% | `ALBERTA` |
| `type` | int | 100% | `3` |
| `active` | boolean | 100% | `True` |

### Term

10 fields · `/api/Customer/Terms` · sampled 6 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `termId` | int | 100% | `4` |
| `code` | string | 100% | `2% Net 10` |
| `description` | string | 100% | `2% Net 10` |
| `discountRate` | decimal | 100% | `0.02` |
| `discountPeriod` | int | 100% | `10` |
| `duePeriod` | int | 100% | `10` |
| `active` | boolean | 100% | `True` |
| `dueDay` | int | 100% | `0` |
| `dueMonths` | int | 100% | `0` |
| `dueMinPeriod` | int | 100% | `0` |

### PriceLevel

10 fields · `/api/Customer/PriceLevels` · sampled 28 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `priceLevelId` | int | 100% | `4` |
| `priceLevelName` | string | 100% | `Bronze` |
| `description` | string | 100% | `Bronze` |
| `active` | boolean | 100% | `True` |
| `customerId` | int | 57% | `1` |
| `defPrice` | boolean | 100% | `False` |
| `basePriceLevelId` | int | 11% | `1` |
| `masterBasePriceLevelId` | int | 96% | `4` |
| `hierarchyLevel` | int | 100% | `0` |
| `remarks` | string | 14% | `test` |

### SOOrderType

9 fields · `/api/SalesOrder/OrderTypes` · sampled 12 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `orderTypeId` | int | 100% | `1` |
| `orderType` | string | 100% | `Other` |
| `description` | string | 100% | `Other Order` |
| `active` | boolean | 100% | `True` |
| `allowFulfilling` | boolean | 100% | `True` |
| `orderTypeCategoryId` | int | 100% | `1` |
| `isSystemType` | boolean | 100% | `False` |
| `baseTypeId` | int | 100% | `1` |
| `allowPrebilling` | boolean | 100% | `True` |

### Priority

7 fields · `/api/ServiceCall/Priorities` · sampled 5 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `priorityID` | int | 100% | `3` |
| `name` | string | 100% | `High` |
| `description` | string | 100% | `High` |
| `rank` | int | 100% | `2` |
| `active` | boolean | 100% | `True` |
| `color` | decimal | 80% | `255` |
| `rankOrder` | int | 100% | `1` |

### ProblemCode

5 fields · `/api/ServiceCall/ProblemCodes` · sampled 4 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `problemCodeId` | int | 100% | `3` |
| `code` | string | 100% | `Damaged` |
| `description` | string | 100% | `Damaged by Customer` |
| `active` | boolean | 100% | `True` |
| `bypassMeterReadingRequirement` | boolean | 100% | `False` |

### RepairCode

4 fields · `/api/ServiceCall/RepairCodes` · sampled 6 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `repairCodeId` | int | 100% | `4` |
| `code` | string | 100% | `Adjusted` |
| `description` | string | 100% | `Adjusted` |
| `active` | boolean | 100% | `True` |

### SLACode

7 fields · `/api/ServiceCall/SLACodes` · sampled 6 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `slaCodeId` | int | 100% | `3` |
| `slaCodeName` | string | 100% | `3 Day` |
| `description` | string | 100% | `3 Day Response` |
| `serviceHourCodeId` | int | 100% | `1` |
| `responseTime` | int | 100% | `1440` |
| `resolutionTime` | int | 50% | `0` |
| `active` | boolean | 100% | `True` |

### NoteType

7 fields · `/api/ServiceCall/NoteTypes` · sampled 11 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `noteTypeId` | int | 100% | `3` |
| `name` | string | 100% | `DTC` |
| `description` | string | 100% | `DeskTech Communications` |
| `isEditable` | boolean | 100% | `False` |
| `isSelectable` | boolean | 100% | `False` |
| `isSystemType` | boolean | 100% | `True` |
| `active` | boolean | 100% | `True` |

### OnHoldCode

15 fields · `/api/ServiceCall/OnHoldCodes` · sampled 13 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `onHoldCodeId` | int | 100% | `4` |
| `code` | string | 100% | `BadSync` |
| `description` | string | 100% | `Bad Data From Remote Client` |
| `useReleaseTimeForResponseCalc` | boolean | 100% | `False` |
| `requireSecurity` | boolean | 100% | `False` |
| `typeId` | int | 100% | `1` |
| `categoryId` | int | 0% |  |
| `systemCode` | boolean | 100% | `True` |
| `active` | boolean | 100% | `True` |
| `allowTechAssign` | boolean | 100% | `False` |
| `allowTechRelease` | boolean | 100% | `False` |
| `stampColor` | int | 100% | `16711680` |
| `includeDescriptionInStamp` | boolean | 100% | `False` |
| `excludeFromResolutionTime` | boolean | 100% | `False` |
| `trackHolds` | boolean | 100% | `True` |

### CancelCode

4 fields · `/api/ServiceCall/CancelCodes` · sampled 3 records

| Field | Type | Filled | Example |
| --- | --- | --- | --- |
| `cancelCodeId` | int | 100% | `1` |
| `code` | string | 100% | `Customer Request` |
| `description` | string | 100% | `Customer Request` |
| `active` | boolean | 100% | `True` |

---

Field names and types come from the vendored OpenAPI document
(`Service Call Client API 2026.07.27`, 94 paths, 78 schemas). Fill rates were measured
against up to 200 live records per entity. Read paths are all verified; the write paths
(`AddCall`, `AddOrder`, `AddMeterReading`) are implemented from the spec and have not
been fired against a live dataset.
