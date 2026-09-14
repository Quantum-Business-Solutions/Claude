# Hotjar finding — posted to the sign-off sheet

**Posted 14 Sep 2026, 14:07 UTC** to *Global notes & rules* on the Praxera Asset Sign-off
as "Quantum (Claude)" (comment `mu1bh76mmj243`). It is note 43 of 43 and sits at the top
of the thread.

> TRACKING — DaVinci's Hotjar snippet is firing on every Praxera page. The tag is commented
> `Hotjar Tracking Code for https://www.davincilabs.com/` and uses DaVinci's site id
> **3845264**, so every Praxera session recording, heatmap and funnel is landing in DaVinci's
> Hotjar account rather than Praxera's. Verified live on `/`, `/get-started`, `/our-process`,
> `/contact` and the three `/alp/ads-*` pages. Before launch this needs either a Praxera
> Hotjar site id or the snippet removed.

Posted with `comment_on_signoff` (portal `6d797a44…`, slug `praxera-asset-signoff`, no group
or row id — that puts it on the sheet's own thread). `update_signoff_sheet` cannot be used on
this sheet: it is the custom two-stage app from `tools/build_signoff_v2.py`, and the tool
refuses it — *"'praxera-asset-signoff' exists in this portal and is not a sign-off sheet."*

## Still to decide

The snippet needs removing or repointing, which is a change to every page's `headHtml`.
Not done — nobody has said which way to go, and a Praxera Hotjar account may not exist yet.
