# Client Discovery (live — no roster file)

The active client list and the code↔company mapping are DERIVED at runtime,
never read from a hand-maintained table. (The legacy 38-row client table went
stale within months; a static roster is always quietly wrong.)

## Deriving the active client list

Active client = a company on the QBS portal (20682069) with open-ticket
associations.

1. Pull open tickets (paginate; exclude internal pipelines by label).
2. For each, pull the ticket→company association. The associated company is
   ground truth for "which client is this."
3. Distinct associated companies = the active client set for this run.

To resolve a client the user names ("clean up Fisher's"), search companies by
name on the QBS portal first, then confirm via that company's associated
tickets. Never resolve a client from subject prefixes alone.

## Learning the 3-letter codes

The `[CODE] - ...` subject prefix is a labeling convention, not an identifier.
Learn it per company, per run:

1. Group that company's tickets and extract the leading `^[A-Z]{2,4} - `
   prefix where present.
2. The dominant prefix across the company's tickets is its code. Record it in
   the run cache alongside the company ID.
3. Use the learned code only for display and subject-pattern matching (shells,
   dupes) — grouping and scoping always go through the association (doctrine
   #4).

## Handling the unknowns (never guess, never error)

- **Company with tickets but no consistent prefix** → work by association;
  note "no stable code" in the report.
- **Prefix that maps to no known company** or to TWO companies (the Spectrum
  problem: same code, two company records) → surface it in the report as a
  data-hygiene finding for the human. Do not pick one silently.
- **Brand-new client** (first tickets appeared since the last pass) → include
  them automatically — this is the point of live discovery — and call them
  out in the summary ("new client detected: [name]").

## Caching

Cache the derived roster (company ID, name, learned code, open-ticket count)
in the working directory for the duration of the run. Refresh on every run —
the cache never persists between sessions and is never committed anywhere.
