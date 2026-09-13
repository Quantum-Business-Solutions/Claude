# Praxera — form notification routing
**Date:** 13 Sep 2026 · **Portal:** 4087538 · Before-state: `backups/form-notify-patrick/`

## Change 1 — Patrick/Nick repointed to QBS
Every Praxera form that notified `patrick@creativesidemarketing.com` (user 3256355) or
`ncampos@creativesidemarketing.com` (66293956) now notifies
`patrick@thequantumleap.business` (**95479787**). Same human, QBS address.

| Form | Before | After |
|---|---|---|
| Praxera - Ingredients & Testing Guide (page form) | 3256355, 4990427 | 95479787, 4990427 |
| Praxera - Ingredients, Testing & Certification Guide | 3256355, 4990427 | 95479787, 4990427 |
| Praxera - Onboarding Guide | 66293956, 3256355 | 95479787 |
| Praxera - Client Onboarding Guide | 66293956, 3256355 | 95479787 |
| Praxera - Supplements Guide | 3256355, 4990427 | 95479787, 4990427 |
| Praxera - Main Lead Form (legacy field set) | 3256355, 4990427 | 95479787, 4990427 |

Where both Patrick and Nick were listed they collapse to one entry.

## Change 2 — main consultation form
`Private Label (Praxera) - Schedule a Consultation` (d8dfdd90), the form on 27 of 35
placements, previously notified **nobody**. Now:
- `notifyContactOwner` = **true**
- recipients = **Sam Fuller** (25112410, FoodScience) + **Patrick Dodge** (95479787, QBS)

## Verification
Re-read via both `/marketing/v3/forms` and `/forms/v2/forms` after each write. On all seven
forms: fieldGroups, displayOptions, legalConsentOptions and the rest of `configuration`
compared byte-for-byte against the backup and are **unchanged**. No Praxera form still lists
3256355 or 66293956.

## Not changed, on purpose
- **111 non-Praxera forms** (DaVinci, Pet Tech, VetriScience, legacy) also list Patrick
  and/or Nick. Left untouched per the standing rule against modifying DaVinci or Pet Tech
  assets. List available on request.
- **User 4990427** is a deleted user still listed on 4 Praxera forms. Not removed — that was
  outside what was asked. It is dead weight, not a misroute, now that Patrick is on each of
  those forms.
