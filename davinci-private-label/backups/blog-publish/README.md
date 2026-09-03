# Publishing the Praxera blog, and restoring the original dates

3 September 2026.

## Published

75 posts existed, all draft. **71 published.** Three were held back deliberately -
"Supplement Dropshipping: 5 Best Tips for Success", "How to Get Started With Dropshipping
Supplements" and "Supplement Dropshipping: Can It Boost Profitability?" - because Tammy had
the dropshipping page pulled the same day: *"I do not want any more of these customers."*
Publishing three posts dedicated to the service would contradict that. One more failed with
a 409 redirect conflict: "Answers to Your Top Questions About Private Label Supplements".

All 75 were scanned before publishing: zero visible DaVinci, zero manufacturing claims, zero
custom formulation in the post copy.

## Dates restored

Publishing put today's date on every post, which reads to a search engine as 75 articles
dumped in one afternoon rather than eight years of accumulated authority.

Matched against the originals in the DaVinci private-label blog (content group 20252938412).
Title matching reached 64 of 75; **matching on the slug tail reached all 75**, after stripping
HubSpot's `-0`, `-0-1` duplicate suffixes. Now spread 2018-2026:

    2018:3  2019:1  2020:1  2021:8  2022:19  2023:8  2024:21  2025:2  2026:12

**Nine of them are not authentic dates.** Those originals carried no `publish_date` at all,
so they fell back to the original's created timestamp, 13 May 2026. Recorded here so nobody
later treats those nine as historical.

`date-remap-plan.json` holds the full old-to-new mapping.

## Same-titled posts - not duplicates

Four posts share the title "Tips for Selling Private Label Supplements on Amazon" and two
share "Tips for Buying Wholesale Private Label Supplements". Their rendered content was
compared: **all six differ** in length and content hash. They are separate versions of the
same article migrated more than once, not copies.

Still worth a human pruning them - six posts covering two topics will compete with each other
for the same query.

**A wrong turn recorded so it is not repeated:** an initial check reported these six as having
empty bodies. That was reading `post_body`, which is empty for these posts. The content lives
in **`widgets`**. All six render 11-13k characters perfectly well.

## Open

- **H1s.** Four of those six render `<h1>Your brand. Our formulations.</h1>` - the page hero -
  instead of the post title. Only two use the real title. If that is widespread, every post is
  handing Google the same H1. A QA pass across all 75 is running.
- **Author bylines.** 13 posts are bylined "DaVinci Healthcare Expert", one "DaVinci Industry
  Expert", one "Dom Orlandi, President of DaVinci". Renaming three author records clears all
  15. 20 posts are already bylined Melinda Elmadjian.
