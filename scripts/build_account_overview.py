#!/usr/bin/env python3
"""Render docs/account-overview.html from the live portal dump.

    python scripts/build_account_overview.py

Reads docs/account-overview-data.json (written by the portal reader) and emits a
standalone page. Every figure on the page carries a provenance chip, because on this
integration the difference between a counted page and a rated duty cycle is the
difference between a quote that holds and one that does not -- and both are just a
number in a box otherwise.

Blanks are rendered as blanks on purpose. 16 of HSBC's leases carry a
contractDetailId and nothing else: no term, no payment, no schedule. A page that hides
that reads as a finished integration.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "docs", "account-overview-data.json")
OUT = os.path.join(HERE, "docs", "account-overview.html")

BASIS_LABEL = {
    "printreleaf_current": ("Counted", "measured",
                            "Pages actually produced, trailing 12 months."),
    "printreleaf_historic": ("Counted", "measured",
                             "Pages actually produced, but in the period shown -- "
                             "a historical rate, not a current one."),
    "actual_12mo": ("Counted", "measured", "e-automate 12-month rolling average."),
    "actual_shorter": ("Counted", "measured", "e-automate 3 or 6-month average."),
    "since_install": ("Counted", "derived", "Average across the whole life of the meter."),
    "mfg_rated": ("Rated", "rated",
                  "Manufacturer duty cycle. What the box can do, not what this "
                  "customer does."),
    "target": ("Target", "rated", "A target, not a measurement."),
    "unknown": ("None", "empty", "No reading history exists on any route."),
}

CSS = """
:root{
  --ground:#f6f7f6; --raise:#ffffff; --sink:#eceeec;
  --ink:#131a1b; --ink-2:#47534f; --ink-3:#79857f;
  --line:#dbe0dc; --line-2:#c6cec8;
  --accent:#0e6b63; --accent-soft:#e2efec;
  --good:#3f6b3a; --warn:#8a4a1c; --bad:#7d2b2b; --colour:#a8681c;
  --measured:#0e6b63; --derived:#4a6b8a; --rated:#8a4a1c; --empty:#8b938e;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --ground:#0f1416; --raise:#161d1f; --sink:#1c2426;
    --ink:#e8edea; --ink-2:#a3b0ab; --ink-3:#77837e;
    --line:#252f31; --line-2:#33403f;
    --accent:#4fbfae; --accent-soft:#15302d;
    --good:#7fb173; --warn:#d1904f; --bad:#d4736c; --colour:#d8a252;
    --measured:#4fbfae; --derived:#8fb2d4; --rated:#d1904f; --empty:#77837e;
  }
}
:root[data-theme="light"]{
  --ground:#f6f7f6; --raise:#ffffff; --sink:#eceeec;
  --ink:#131a1b; --ink-2:#47534f; --ink-3:#79857f;
  --line:#dbe0dc; --line-2:#c6cec8;
  --accent:#0e6b63; --accent-soft:#e2efec;
  --good:#3f6b3a; --warn:#8a4a1c; --bad:#7d2b2b; --colour:#a8681c;
  --measured:#0e6b63; --derived:#4a6b8a; --rated:#8a4a1c; --empty:#8b938e;
}
:root[data-theme="dark"]{
  --ground:#0f1416; --raise:#161d1f; --sink:#1c2426;
  --ink:#e8edea; --ink-2:#a3b0ab; --ink-3:#77837e;
  --line:#252f31; --line-2:#33403f;
  --accent:#4fbfae; --accent-soft:#15302d;
  --good:#7fb173; --warn:#d1904f; --bad:#d4736c; --colour:#d8a252;
  --measured:#4fbfae; --derived:#8fb2d4; --rated:#d1904f; --empty:#77837e;
}

*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:34px 22px 80px}

.eyebrow{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--ink-3);display:flex;flex-wrap:wrap;gap:9px;
  align-items:center}
.eyebrow b{color:var(--accent);font-weight:600}
h1{font-size:clamp(27px,4.1vw,40px);line-height:1.08;letter-spacing:-.023em;
  font-weight:760;margin:13px 0 10px;text-wrap:balance;max-width:23ch}
.lede{color:var(--ink-2);max-width:66ch;margin:0}
.lede code{font-family:var(--mono);font-size:.88em;background:var(--sink);
  padding:1px 5px;border-radius:3px}

/* account switcher */
.picker{display:flex;flex-wrap:wrap;gap:7px;margin:26px 0 22px;
  border-top:1px solid var(--line);padding-top:20px}
.pick{font-family:var(--mono);font-size:11.5px;letter-spacing:.02em;
  background:var(--raise);color:var(--ink-2);border:1px solid var(--line);
  padding:7px 11px;border-radius:2px;cursor:pointer;text-align:left;
  transition:border-color .13s,color .13s}
.pick:hover{border-color:var(--line-2);color:var(--ink)}
.pick[aria-pressed="true"]{border-color:var(--accent);color:var(--ink);
  background:var(--accent-soft);box-shadow:inset 2px 0 0 var(--accent)}
.pick:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.pick .n{display:block;font-family:var(--sans);font-size:13px;font-weight:600;
  letter-spacing:0;margin-bottom:1px}

/* record shell */
.shell{display:grid;grid-template-columns:296px minmax(0,1fr);gap:20px;
  align-items:start}
@media (max-width:900px){.shell{grid-template-columns:minmax(0,1fr)}}

.card{background:var(--raise);border:1px solid var(--line);border-radius:3px}
.card>h3{margin:0;padding:11px 14px;border-bottom:1px solid var(--line);
  font-family:var(--mono);font-size:10.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-3);font-weight:600;
  display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.card>h3 .cnt{color:var(--accent)}

/* left rail summary */
.rail{display:flex;flex-direction:column;gap:14px;position:sticky;top:18px}
@media (max-width:900px){.rail{position:static}}
.who{padding:14px}
.who .nm{font-size:19px;font-weight:680;letter-spacing:-.014em;line-height:1.2}
.who .loc{color:var(--ink-3);font-size:13px;margin-top:2px}
.who .cust{font-family:var(--mono);font-size:11px;color:var(--accent);
  margin-top:8px;letter-spacing:.03em}

.hero-fig{padding:14px;border-bottom:1px solid var(--line)}
.hero-fig .v{font-family:var(--mono);font-size:31px;font-weight:600;
  letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1}
.hero-fig .u{font-family:var(--mono);font-size:10.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-3);margin-top:5px}

dl.props{margin:0;padding:4px 0}
dl.props>div{display:flex;justify-content:space-between;gap:12px;align-items:baseline;
  padding:6px 14px}
dl.props dt{color:var(--ink-2);font-size:13px;margin:0}
dl.props dd{margin:0;font-family:var(--mono);font-size:13px;font-weight:600;
  font-variant-numeric:tabular-nums;text-align:right}
dl.props dd.blank{color:var(--empty);font-weight:400}

/* provenance chip */
.chip{display:inline-flex;align-items:center;gap:4px;font-family:var(--mono);
  font-size:9.5px;letter-spacing:.09em;text-transform:uppercase;
  padding:2px 5px;border-radius:2px;border:1px solid currentColor;
  font-weight:600;white-space:nowrap}
.chip.measured{color:var(--measured)}
.chip.derived{color:var(--derived)}
.chip.rated{color:var(--rated)}
.chip.empty{color:var(--empty)}
.provline{padding:10px 14px;border-top:1px solid var(--line);
  color:var(--ink-3);font-size:12px;line-height:1.45}

/* tables */
.tables{display:flex;flex-direction:column;gap:20px;min-width:0}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);font-weight:600;text-align:left;padding:8px 11px;
  border-bottom:1px solid var(--line);white-space:nowrap;background:var(--raise)}
td{padding:8px 11px;border-bottom:1px solid var(--line);white-space:nowrap;
  font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
tbody tr:hover td{background:var(--sink)}
td.id{font-family:var(--mono);font-weight:600;letter-spacing:.01em}
td.num{font-family:var(--mono);text-align:right}
td.mono{font-family:var(--mono);color:var(--ink-2)}
td.blank{color:var(--empty)}
td.blank::after{content:"—"}

.state{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:600;
  letter-spacing:.07em;text-transform:uppercase;padding:1px 6px;border-radius:2px}
.state.good{color:var(--good);box-shadow:inset 0 0 0 1px currentColor}
.state.warn{color:var(--warn);box-shadow:inset 0 0 0 1px currentColor}
.state.bad{color:var(--bad);box-shadow:inset 0 0 0 1px currentColor}

.empty-note{padding:16px 14px;color:var(--ink-3);font-size:13px;line-height:1.5}
.empty-note b{color:var(--ink-2);font-weight:600}

/* colour split bar */
.split{display:flex;height:5px;border-radius:3px;overflow:hidden;margin:9px 14px 4px;
  background:var(--sink)}
.split i{display:block;height:100%}
.split-key{display:flex;gap:13px;padding:0 14px 11px;font-family:var(--mono);
  font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
.split-key span{display:flex;align-items:center;gap:4px}
.split-key i{width:8px;height:8px;border-radius:1px;display:block}

footer{margin-top:44px;padding-top:20px;border-top:1px solid var(--line);
  color:var(--ink-3);font-size:12.5px;line-height:1.6;max-width:74ch}
footer b{color:var(--ink-2)}
footer code{font-family:var(--mono);font-size:.9em}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""


def esc(v) -> str:
    return html.escape(str(v))


def n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fmt(v, dp=0, dash="—"):
    f = n(v)
    if f is None:
        return dash
    return f"{f:,.{dp}f}"


def chip(kind: str, label: str) -> str:
    return f'<span class="chip {kind}">{esc(label)}</span>'


def expiry_state(iso: str | None):
    """current / expiring within a year / expired, judged against today."""
    if not iso:
        return ("", "")
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return ("", "")
    today = dt.date.today()
    if d < today:
        return ("bad", "expired")
    if (d - today).days <= 365:
        return ("warn", "< 1 yr")
    return ("good", "current")


def rail(rec: dict) -> str:
    p = rec["props"]
    basis = p.get("ea_fleet_volume_basis") or "unknown"
    blab, bkind, bwhy = BASIS_LABEL.get(basis, BASIS_LABEL["unknown"])
    period = p.get("ea_fleet_volume_period")
    vol = n(p.get("ea_fleet_monthly_volume")) or 0
    colour = n(p.get("ea_fleet_color_pct"))
    exp = p.get("ea_fleet_next_expiry")
    st, stlab = expiry_state(exp)

    rows = [
        ("Machines", fmt(p.get("ea_fleet_machine_count")), "measured"),
        ("Meters", fmt(p.get("ea_fleet_meter_count")), "measured"),
        ("Contracts", fmt(p.get("ea_fleet_contract_count")), "measured"),
        ("Leases", fmt(p.get("ea_fleet_lease_count")), "measured"),
        ("Open service calls", fmt(p.get("ea_fleet_open_calls")), "measured"),
        ("Spend / month", "$" + fmt(p.get("ea_fleet_monthly_spend")), "derived"),
        ("Lifetime pages", fmt(p.get("ea_fleet_lifetime_pages")), "measured"),
    ]
    body = "".join(
        '<div><dt>' + esc(lbl) + '</dt><dd'
        + (' class="blank"' if val == "—" else '')
        + '>' + esc(val) + '</dd></div>'
        for lbl, val, _ in rows)

    split = ""
    if colour is not None and vol:
        bw = max(0.0, 100.0 - colour)
        split = (
            f'<div class="split">'
            f'<i style="width:{bw:.1f}%;background:var(--ink-3)"></i>'
            f'<i style="width:{colour:.1f}%;background:var(--colour)"></i></div>'
            f'<div class="split-key">'
            f'<span><i style="background:var(--ink-3)"></i>mono {bw:.0f}%</span>'
            f'<span><i style="background:var(--colour)"></i>colour {colour:.0f}%</span>'
            f'</div>')

    return f"""
<div class="rail">
  <div class="card">
    <div class="who">
      <div class="nm">{esc(p.get('name') or '')}</div>
      <div class="loc">{esc(', '.join(x for x in (p.get('city'), p.get('state')) if x))}</div>
      <div class="cust">{esc(p.get('ea_customer_number') or '')}</div>
    </div>
  </div>

  <div class="card">
    <h3>e-Automate Fleet Summary</h3>
    <div class="hero-fig">
      <div class="v">{fmt(vol)}</div>
      <div class="u">pages / month</div>
      <div style="margin-top:9px;display:flex;gap:6px;flex-wrap:wrap">
        {chip(bkind, blab)}{f'<span class="chip {bkind}">{esc(period)}</span>' if period else ''}
      </div>
    </div>
    {split}
    <dl class="props">{body}</dl>
    <div class="provline"><b>Next expiry</b>
      &nbsp;<span style="font-family:var(--mono)">{esc(exp or '—')}</span>
      {f'&nbsp;<span class="state {st}">{stlab}</span>' if st else ''}
    </div>
    <div class="provline">{esc(bwhy)}</div>
  </div>
</div>"""


def table(title: str, cols: list[str], rows: list[list[str]], note: str = "") -> str:
    if not rows:
        return (f'<section class="card"><h3>{esc(title)}<span class="cnt">0</span></h3>'
                f'<div class="empty-note">{note or "Nothing associated."}</div></section>')
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(rows_) + "</tr>" for rows_ in rows)
    extra = f'<div class="empty-note">{note}</div>' if note else ""
    return (f'<section class="card"><h3>{esc(title)}'
            f'<span class="cnt">{len(rows)}</span></h3>'
            f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>{extra}</section>')


def cell(v, kind="mono"):
    if v in (None, "", "None"):
        return '<td class="blank"></td>'
    return f'<td class="{kind}">{esc(v)}</td>'


def tables(rec: dict) -> str:
    ch = rec["children"]
    out = []

    eq = [[f'<td class="id">{esc(r.get("ea_equipment_number") or "—")}</td>',
           cell(r.get("ea_serial_number")),
           cell(", ".join(x for x in (r.get("ea_city"), r.get("ea_state")) if x) or None),
           cell(r.get("ea_location_description")),
           cell(r.get("install_date")),
           cell(r.get("ea_warranty_date"))]
          for r in sorted(ch.get("equipment", []),
                          key=lambda x: str(x.get("ea_equipment_number") or ""))]
    out.append(table("Equipment",
                     ["Equipment #", "Serial", "Location", "Description",
                      "Installed", "Warranty"], eq,
                     "Install date and description are blank because e-automate has "
                     "them blank, not because they were not mapped."))

    cn = []
    for r in sorted(ch.get("contract", []),
                    key=lambda x: str(x.get("ea_exp_date") or "9999")):
        st, lab = expiry_state(r.get("ea_exp_date"))
        rate = n(r.get("base_rate"))
        cn.append([f'<td class="id">{esc(r.get("ea_contract_number") or "—")}</td>',
                   cell(r.get("start_date")),
                   cell(r.get("ea_exp_date")),
                   (f'<td><span class="state {st}">{lab}</span></td>' if st
                    else '<td class="blank"></td>'),
                   (f'<td class="num">${rate:,.0f}</td>' if rate is not None
                    else '<td class="blank"></td>'),
                   cell("Yes" if str(r.get("ea_renewable")) == "true" else
                        ("No" if r.get("ea_renewable") is not None else None))])
    out.append(table("Contracts",
                     ["Contract #", "Start", "Expires", "State", "Base rate",
                      "Renewable"], cn))

    ls = [[f'<td class="id">{esc(r.get("ea_contract_detail_id") or "—")}</td>',
           cell(r.get("ea_lease_schedule")),
           cell(r.get("ea_lease_term")),
           cell(r.get("ea_lease_payment_amount")),
           cell(r.get("ea_lease_payment_end_date")),
           cell(r.get("ea_lease_principal_balance"))]
          for r in ch.get("lease", [])]
    out.append(table("Leases",
                     ["Detail ID", "Schedule", "Term", "Payment", "Ends",
                      "Principal"], ls,
                     "<b>This is the honest state of the lease side.</b> The records "
                     "and the associations are correct, and every term is blank: of "
                     "2,981 contract lines in the sandbox only 45 are leases and only "
                     "one carries actual terms. The columns are built and waiting for "
                     "a dealer whose lease data is filled in."))

    sc = []
    for r in sorted(ch.get("service_call", []),
                    key=lambda x: str(x.get("ea_date") or ""), reverse=True):
        stat = str(r.get("ea_status") or "").strip()
        closed = stat.upper().startswith("C")
        sc.append([f'<td class="id">{esc(r.get("ea_call_number") or "—")}</td>',
                   cell(r.get("ea_date")),
                   cell(r.get("ea_equipment_number")),
                   (f'<td><span class="state {"good" if closed else "warn"}">'
                    f'{esc(stat)}</span></td>' if stat else '<td class="blank"></td>'),
                   cell(r.get("ea_description")),
                   cell(r.get("ea_close_date"))])
    out.append(table("Service Calls",
                     ["Call #", "Opened", "Equipment #", "Status", "Description",
                      "Closed"], sc,
                     "Equipment # here was blank on every record until the call was "
                     "re-read from <code>ByCallNumber</code> -- the list route returns "
                     "it as null."))

    meters = ch.get("meter", [])
    mt = [[f'<td class="id">{esc(r.get("ea_equipment_number") or "—")}</td>',
           cell(r.get("ea_meter_type_code")),
           cell("Default" if str(r.get("ea_is_default")) == "true" else "—"),
           cell(r.get("ea_meter_digits"))]
          for r in sorted(meters, key=lambda x: (str(x.get("ea_equipment_number") or ""),
                                                 str(x.get("ea_meter_type_code") or "")))]
    out.append(table("Meters", ["Equipment #", "Type", "Default", "Digits"], mt,
                     "No volume columns, deliberately: every average on every meter in "
                     "this sandbox reads 0. The fleet volume above comes from "
                     "PrintReleaf, which counts pages actually produced."))

    return '<div class="tables">' + "".join(out) + "</div>"


def main() -> None:
    recs = json.load(open(DATA))
    for r in recs:
        r["props"].setdefault("name", "(unnamed)")

    picks = "".join(
        f'<button class="pick" type="button" data-i="{i}" '
        f'aria-pressed="{"true" if i == 0 else "false"}">'
        f'<span class="n">{esc(r["props"].get("name"))}</span>'
        f'{fmt(r["props"].get("ea_fleet_monthly_volume"))} pg/mo &middot; '
        f'{esc(r["props"].get("ea_fleet_machine_count") or 0)} mach &middot; '
        f'{esc(r["props"].get("ea_fleet_contract_count") or 0)} ctr'
        f'</button>' for i, r in enumerate(recs))

    panels = "".join(
        f'<div class="shell" data-panel="{i}"'
        f'{"" if i == 0 else " hidden"}>{rail(r)}{tables(r)}</div>'
        for i, r in enumerate(recs))

    total_vol = sum(n(r["props"].get("ea_fleet_monthly_volume")) or 0 for r in recs)

    doc = f"""<title>Account overview on a HubSpot company record</title>
<style>{CSS}</style>
<div class="wrap">
  <p class="eyebrow"><b>Live portal 47404459</b><span>&middot;</span>
    <span>{len(recs)} accounts</span><span>&middot;</span>
    <span>{total_vol:,.0f} pages/month across them</span><span>&middot;</span>
    <span>read {dt.date.today().isoformat()}</span></p>

  <h1>What the account overview looks like on the record</h1>
  <p class="lede">The left rail is the <code>e-Automate Fleet Summary</code> property
  group, live on all 160 companies in the portal right now &mdash; open a company,
  <em>View all properties</em>, and it is there. The tables on the right are the
  association cards. Every figure carries where it came from, because a counted page
  and a rated duty cycle are the same number in a box and a very different quote.</p>

  <div class="picker">{picks}</div>
  {panels}

  <footer>
    <p><b>What is real and what is not.</b> Every number here was read out of HubSpot,
    which had it from CEO Juice. The blanks are real too &mdash; lease terms, install
    dates and meter volumes are empty in the source, and showing them empty is the
    point. The one thing on this page that is a mock-up is the arrangement: HubSpot
    puts the property group behind <em>View all properties</em> until somebody pins it
    to the sidebar in <b>Settings &rarr; Objects &rarr; Companies &rarr; Record
    customization</b>, which is a UI-only setting with no API behind it.</p>
    <p><b>Volume does not come from meters.</b> All 84 meters reachable across 120
    machines report 0 for every average, including the manufacturer rating. The figure
    above is from <code>/api/PrintReleaf/customers/{{id}}</code>, which counts pages
    produced inside a window you specify &mdash; so the period is shown next to it. A
    trailing-twelve-month query returns nothing here because this sandbox's data
    largely stops years ago; that is a property of the sandbox, not of the route.</p>
  </footer>
</div>
<script>
(function(){{
  var picks=[].slice.call(document.querySelectorAll('.pick'));
  var panels=[].slice.call(document.querySelectorAll('[data-panel]'));
  picks.forEach(function(b){{
    b.addEventListener('click',function(){{
      var i=b.getAttribute('data-i');
      picks.forEach(function(o){{o.setAttribute('aria-pressed',o===b?'true':'false');}});
      panels.forEach(function(p){{p.hidden=p.getAttribute('data-panel')!==i;}});
    }});
  }});
}})();
</script>
"""
    with open(OUT, "w") as fh:
        fh.write(doc)
    print(f"wrote {OUT} ({len(doc):,} bytes, {len(recs)} accounts)")


if __name__ == "__main__":
    main()
