# Judge rubric

Judge model: `claude-opus-5`. One call per trial, blind pairwise.

The judge sees:
1. The same real per-portal input the two candidates saw (company context,
   meeting notes, HubSpot context).
2. Two drafted proposals labeled **A** and **B**, order randomized per
   trial (coin flip, not by model or portal order) so position bias can't
   correlate with model identity.

It does **not** see which model produced which label. The mapping is decoded
only after the verdict is recorded, when computing aggregate win rates.

## Instructions given to the judge

```
You are reviewing two drafts of the same client proposal, labeled A and B.
Both were given the same client context, shown above. Decide which is the
stronger proposal a QBS account manager could send with the least editing,
using these criteria in order of importance:

1. Grounding — does it accurately reflect the client's actual situation and
   stated priorities from the meeting notes/HubSpot context, without
   inventing details the input doesn't support?
2. Scope fit — is the recommended scope of work the right size and shape
   for this client, not generic or copy-pasted?
3. Persuasiveness and clarity — would this proposal read as compelling and
   professional to the client, not just internally consistent?
4. Completeness — overview, scope, pricing/investment framing, and next
   steps all present and coherent.
5. Pricing judgment — where a number or range is given, is it reasonable
   given the scope and any deal-value signals in the input?

Respond with:
- "winner": "A" or "B" (or "tie" only if you truly cannot separate them)
- "rationale": 2-4 sentences citing specific evidence from the drafts
- "confidence": "low" | "medium" | "high"
```

## Aggregate reporting

- Win rate per model (ties counted as half a win each).
- Win rate broken out separately by which position (A/B) each model landed
  in, to check for judge position bias.
- All rationales kept in `results/` (gitignored) for spot-checking; a
  disagreement between rationale and stated winner invalidates that trial.
