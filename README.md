# Claude

## Section 179 vehicle depreciation chart

`section-179-depreciation-chart.html` — a self-contained, interactive five-year
depreciation chart for Section 179 eligible vehicles, current for **tax year 2026**.

Pick any of 60+ vehicles (or type your own price) and it charts the deduction across
all six tax years under three strategies:

| Strategy | What it models |
|---|---|
| §179 + 100% bonus | Maximum acceleration — the whole basis in year one |
| §179, bonus elected out | $32,000 §179, then MACRS on the remainder |
| Straight MACRS | 20 / 32 / 19.2 / 11.52 / 11.52 / 5.76% |

Vehicles are split by the three treatments that actually govern the result:

- **Full §179** — cargo bed ≥ 6 ft, cargo van, 9+ passenger shuttle, or GVWR > 14,000 lb
- **$32,000 SUV cap** — GVWR 6,001–14,000 lb (Urus, G-Wagon, Escalade, Model X …)
- **§280F capped** — GVWR ≤ 6,000 lb, limited to $20,300 in year one

### 2026 figures used

| Item | Amount | Source |
|---|---|---|
| §179 ceiling | $2,560,000 (phase-out at $4,090,000) | Rev. Proc. 2025-32 |
| Heavy SUV §179 cap | $32,000 | Rev. Proc. 2025-32 |
| Bonus depreciation | 100%, permanent | OBBBA §70301 |
| §280F year 1 | $20,300 with bonus / $12,300 without | Rev. Proc. 2026-15 |
| §280F years 2 / 3 / 4+ | $19,800 / $11,900 / $7,160 | Rev. Proc. 2026-15 |

No build step and no external requests — open the file in a browser. Light and dark
themes both supported; the chart palette is validated for colorblind separation.

Estimates for planning discussion only, not tax advice.
