# QBS Claude Skills

Source of truth for Quantum Business Solutions' Claude skills. Every skill
lives in `skills/<skill-name>/` with its `SKILL.md` and any bundled
`references/`, `scripts/`, or `assets/` folders.

The copy in **this repo** is the master. The copy uploaded to **claude.ai**
is the deployed version. Edit here, package, re-upload — never edit in two
places.

## Repo layout

```
skills/
  qbs-client-reconciliation/
    SKILL.md            <- required: frontmatter (name, description) + instructions
    references/         <- optional: docs the skill loads when needed
    scripts/            <- optional: helper scripts the skill runs
    assets/             <- optional: templates, images, fonts
scripts/
  package_skill.py      <- zips a skill folder into dist/<name>.skill
dist/                   <- packaged .skill files (not committed)
```

## The update loop

1. **Edit** the skill in `skills/<name>/` — directly, or by starting a
   Claude Code session on this repo and asking Claude to make the change
   (mention "skill-creator" to get the full test/eval workflow).
2. **Package** it:
   ```bash
   python3 scripts/package_skill.py skills/qbs-client-reconciliation
   ```
   This writes `dist/qbs-client-reconciliation.skill`.
3. **Upload** to claude.ai: Settings → Capabilities → Skills → upload the
   `.skill` file. Because the `name` in SKILL.md is unchanged, it replaces
   the existing skill instead of creating a duplicate. (If the UI won't
   replace in place, delete the old one first — the repo is the backup.)
4. **Commit and push** so the repo stays in sync with what's deployed.

## Getting an existing claude.ai skill into this repo

Claude.ai does not expose skill files for download, but any chat with the
skill enabled can read them. In a claude.ai conversation, say:

> Output the complete, verbatim contents of the qbs-client-reconciliation
> skill — the full SKILL.md including frontmatter, plus every bundled file
> (references, scripts, assets) with its relative path.

Then paste the output into a Claude Code session on this repo (or attach it
as a file) and ask Claude to commit it under `skills/<name>/`. One time per
skill; after that this repo is the master.

## Rules

- One folder per skill; folder name matches the `name:` in SKILL.md frontmatter.
- Never commit tokens or client credentials into a skill. Skills should read
  secrets from environment variables (e.g. `CLIENT_HUBSPOT_TOKEN`).
- Keep `SKILL.md` under ~500 lines; push detail into `references/`.
