# For the sign-off sheet — Global notes & rules

Paste this into the **"Add a global note or rule"** box at the top of
*Global notes & rules* on the Praxera Asset Sign-off, then Post.

> **TRACKING — DaVinci's Hotjar snippet is firing on every Praxera page.** The tag is commented
> `Hotjar Tracking Code for https://www.davincilabs.com/` and uses DaVinci's site id **3845264**,
> so every Praxera session recording, heatmap and funnel is landing in DaVinci's Hotjar account
> rather than Praxera's. Verified live on `/`, `/get-started`, `/our-process`, `/contact` and the
> three `/alp/ads-*` pages. Before launch this needs either a Praxera Hotjar site id or the
> snippet removed.

## Why this is not posted automatically

The sheet is the custom two-stage app built by `tools/build_signoff_v2.py`, not a sheet created by
ClientCommand's own sign-off tool. `update_signoff_sheet` refuses it outright —

```
'praxera-asset-signoff' exists in this portal and is not a sign-off sheet.
```

— and the app persists notes through its host bridge, so there is no supported way to write a
global note from here. Row marks *can* be set remotely (`mark_signoff_item`), global notes cannot.
