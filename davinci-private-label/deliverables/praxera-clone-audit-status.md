# Praxera cloned assets — launch-readiness status (8 Sep 2026)

Scope: the workflows, emails and forms cloned from DaVinci for Praxera in late August.
Everything below was read from the live portal today. Nothing on DaVinci or PetTech was changed.

## Summary

| Asset | Count | State | Ready? |
|---|---|---|---|
| Forms on Praxera pages | 34 pages carry a Praxera form, 0 carry another brand's | live | **Yes** |
| Workflows | 12, all disabled | staged | **Yes, once switched on** — see notes |
| Emails | 111, all draft | staged | **Not yet** — reply-to and 7 copy decisions open |

## Workflows — what was found and fixed

- All 94 email sends already pointed at Praxera emails. The clone copied sends correctly.
- **Fixed:** 5 flows enrolled on "Contact Us NEW" (a DaVinci form) alongside the Praxera one.
  23 references swapped to "Praxera - Contact Us". Verified by read-back; flows still off.
- **Lists are unchanged by design.** This is a rebrand, so the flows keep the same audience
  lists. 7 lists with DaVinci-era names are correct.
- **10 list references point at deleted lists.** All 10 are inherited verbatim from the
  DaVinci originals, which are enabled and running with them today. Every affected flow also
  enrols from a Praxera form, so nothing is blocked. Hygiene item for Justin, both sets.
- **Open:** the Sales-Qualified flow still triggers on a deleted form and on
  "Brand Development Call (Inactive)" from 2019. Recommend removing both triggers.

## Emails — what was found and fixed

- From name "Praxera" on all 111. No DaVinci in any subject or visible copy.
- **Fixed:** 5 manufacturing claims reworded to the approved form ("made in FDA-inspected,
  GMP-certified U.S. facilities"). A sweep of all 111 now finds none.
- **Fixed:** 96 review-highlight markers (pink/red, would have rendered if sent) stripped from
  53 emails. 7 kept, deliberately, so the copy stays flagged in the editor until the client rules.
- **Open — needs Tammy:** reply-to is `enews@davincilabs.com` on 108 emails. The domain
  `praxerasupplements.com` is connected for sending, but no Praxera mailbox exists yet.
  Someone at FoodScience has to own the inbox before it can be set.
- **Open — needs Tammy (3 emails):** "we guarantee" ×3, "family-owned company" ×2,
  "purest and most potent ingredients" ×2.
- **Left as is (Shawn):** 80 footers link DaVinci Twitter/Instagram; Praxera has no socials yet.
- **Not touched, by rule:** images served from `info.davincilabs.com` / `www.pettechlabs.com`.
  That is the portal's shared file-hosting domain; changing it is a portal-wide setting.

## Also open, on the website (not clone-related)

- FAQ answer on 17 category pages still says "we handle production… we produce". Approval
  sheet with proposed wording: `faq-manufacturing-wording-for-approval.md`. Nothing live changed.
- `PL - Heritage (Section)` module should be retired from the theme now that every page uses
  the global, so it cannot be picked again.

Backups: `backups/workflow-enrolment/`, `backups/email-mfg-claims/`, `backups/email-review-spans/`.
