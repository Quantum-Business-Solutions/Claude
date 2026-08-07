# V1 STYLE SPEC — measured from 1.53M chars of the 63 original pages
Occurrence counts in brackets. These are the numbers to match.

## Type scale (font-size)
17px [855]  body copy — THE default body size
15px [689]  secondary / card body / small print
32px [337]  h2 section headings
18px [337]  lead paragraph
12px [329] · 13px [319] · 14px [305]  eyebrows, labels, fine print
24px [285]  h3 card titles
16px [265]  buttons
19px [219]
34px [134]  larger h2
48px [87]   stat numerals
56px [81]   step numerals (01/02/03)

## Card treatment
border-top: 4px solid #6BA644   [165]  <-- the green accent. PRIMARY card style.
border-top: 4px solid #012638   [36]   <-- navy variant (spec cards)
border-top: 1px solid rgba(255,255,255,.12) [62]  <-- on dark backgrounds
border-radius: 10px [262] · 12px [206] · 8px [253] · 6px [485]
box-shadow: 0 1px 4px rgba(1,38,56,.04)  [284]
box-shadow: 0 2px 12px rgba(1,38,56,.06) [165]
box-shadow: 0 4px 16px rgba(1,38,56,.08) [142]
box-shadow: 0 8px 30px rgba(1,38,56,.15) [45]  (hover / elevated)

## Icon tile — EXACT, this is what V2 lost
display:inline-flex; align-items:center; justify-content:center;
width:56px; height:56px; background:#c9dbe2; border-radius:12px; margin:0 0 18px;
(smaller variant: 48px / radius 10px / margin 0 0 16px)

## Spacing
section padding: 90px 20px [192] · 80px 20px [169]
card padding:    22px 28px [282] · 28px 26px [125] · 34px 30px [165]
pill padding:    4px 10px [262]
grid gap: 50px [55] · 28px [52] · 24px [50] · 56px [45] · 40px [34] · 60px [33]

## letter-spacing
2px [314]   eyebrows / uppercase kickers
1.5px [236] uppercase labels
.5px [168]  buttons
.2px [62]   fine print

## Button (unchanged, 169 instances)
display:inline-block; background:#6BA644; color:#fff; padding:16px 38px;
text-decoration:none; font-size:16px; font-weight:700; border-radius:4px; letter-spacing:.5px;

## Colours
#6BA644 green · #012638 navy · #c9dbe2 pale blue · #e6e5e3 stone · #f7f7f6 off-white
