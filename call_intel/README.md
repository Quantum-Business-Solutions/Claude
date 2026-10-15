# Call Intel

Turns call transcripts into structured HubSpot data and keeps it current weekly.

## What it does
1. **Transcript sync** - pulls ConnectAndSell conversations and writes the transcript onto the matching HubSpot call record (`Transcript`, `Transcript Source`).
2. **Scoring** - every new call is scored:
   - *Hybrid* (calls with a transcript): TypeSafe **Jev** answers the typed yes/no and pick-one fields (used only when it is decisive), one fast Gemini call fills the text, quote and judgment fields. Company signals (CRM, dialer, data tool, HubSpot status, outsourcing, budget, contract and lease end dates, each with a quote) and rep coaching (opener, meeting ask and when, closes, objections, decision maker, call stage).
   - *Notes pass* (no transcript): signals only, from HubSpot's AI summary / tracked terms / typed notes. Marked `call_summary`, and upgraded automatically if a transcript later appears.
3. **Roll-up** - signals roll up to the company (newest call wins). `HubSpot status = active` needs the *prospect's own words*; a rep's assertion is `unconfirmed`. Hand-entered values in `Currently Using HubSpot?` / `HubSpot Intent Company` change only when the call is newer than the edit **and** high confidence.
4. **Tasks** - one task per company entering *Considering HubSpot* with no meeting booked.
5. **Stats** - `call_intel_stats.json` (totals and percentages only) feeds the Call Intel section of the Call Analysis page.

## Run
```
python3 weekly.py            # dry run
python3 weekly.py --apply    # last 7 days of calls only
python3 weekly.py --days 3 --apply
```
HubSpot search lags behind writes by minutes, so the job lists a window's call ids with search and then *reads* their properties.

## Environment (no secrets in the repo)
`HUBSPOT_TOKEN` (or `QBS_HUBSPOT_TOKEN`), `GOOGLE_GEMINI_KEY`, `JEV_API_KEY`, `CAS_USER_ID`, `CAS_PASSWORD`, `CAS_API_KEY`, `CAS_SECRET_KEY`,
`HUBSPOT_PORTAL_ID`, `CI_TASK_OWNER_ID` (owner id that receives tasks). Optional: `CI_COACH_PREFIX` (default `cas_coach_`), `CI_TRANSCRIPT_PROP` (default `cas_transcript`), `CI_AI_NOTES_PROP`.

## Notes
- HubSpot-native call transcripts are not readable through the API (third-party transcript endpoint only); those calls use summaries.
- Property definitions live in the ClientCommand package `call-intel`.
