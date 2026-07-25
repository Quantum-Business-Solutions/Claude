#!/usr/bin/env node
/**
 * Seeds the taste library with a few live-site references whose tokens were
 * read via Firecrawl's `branding` extractor. Run once to have real measured
 * data in the library instead of an empty gallery:
 *
 *   node mcp-server/src/seed.mjs
 *
 * Safe to re-run — it skips any sourceUrl already present.
 */
import { addReference, readAll } from "./store.js";

const seeds = [
  {
    title: "Linear",
    sourceUrl: "https://linear.app",
    sourceKind: "live-site",
    project: "both",
    category: "SaaS product marketing",
    tags: ["minimal", "dark-mode", "restrained-motion", "product-led"],
    notes:
      "The reference point for restrained dark product marketing: near-black ground, a single indigo link accent, and a tight 2px radius throughout. Almost no decoration — hierarchy is carried entirely by type weight and spacing.",
    guardrails: [
      "keep one saturated accent; let the ground stay near-black",
      "do not soften the radius into pill-shaped cards",
    ],
    tokens: {
      colorScheme: "dark",
      colors: {
        primary: "#D0D6E0",
        secondary: "#E4F222",
        accent: "#E5E5E6",
        background: "#08090A",
        textPrimary: "#08090A",
        link: "#5E6AD2",
      },
      fonts: [
        { family: "Inter", role: "body" },
        { family: "SF Pro Display", role: "heading" },
      ],
      fontSizes: { h1: "64px", h2: "48px", body: "15px" },
      spacing: { baseUnit: 8, borderRadius: "2px" },
      components: {
        buttonPrimary: { background: "#E5E5E6", textColor: "#08090A", borderRadius: "9999px" },
        buttonSecondary: { background: "#141516", textColor: "#F7F8F8", borderRadius: "9999px" },
      },
      personality: { tone: "modern", energy: "medium", targetAudience: "tech-savvy professionals" },
      designSystem: { framework: "custom" },
      confidence: { overall: 0.925 },
    },
  },
  {
    title: "Stripe",
    sourceUrl: "https://stripe.com",
    sourceKind: "live-site",
    project: "both",
    category: "B2B fintech / trust-first",
    tags: ["trust-first", "light-ground", "single-accent", "enterprise"],
    notes:
      "How to look credible to a procurement panel without looking dull: white ground, near-black text, and one confident indigo (#533AFD) reserved for links and the primary CTA. Sohne over a generic sans is a large part of why it reads bespoke.",
    guardrails: [
      "reserve the accent for links and the primary CTA only",
      "avoid a generic system sans — the typeface is doing real brand work",
    ],
    tokens: {
      colorScheme: "light",
      colors: {
        primary: "#061B31",
        secondary: "#FFE0D1",
        accent: "#533AFD",
        background: "#FFFFFF",
        textPrimary: "#533AFD",
        link: "#533AFD",
      },
      fonts: [
        { family: "Sohne", role: "body" },
        { family: "SF Pro Display", role: "heading" },
      ],
      fontSizes: { h1: "48px", h2: "32px", body: "32px" },
      spacing: { baseUnit: 8, borderRadius: "0px" },
      components: {
        buttonPrimary: { background: "#533AFD", textColor: "#FFFFFF", borderRadius: "4px" },
        buttonSecondary: {
          background: "#FFFFFF",
          textColor: "#533AFD",
          borderColor: "#B9B9F9",
          borderRadius: "4px",
        },
      },
      personality: {
        tone: "professional",
        energy: "medium",
        targetAudience: "businesses and developers",
      },
      designSystem: { framework: "custom" },
      confidence: { overall: 0.925 },
    },
  },
  {
    title: "Orbit Media Studios",
    sourceUrl: "https://www.orbitmedia.com",
    sourceKind: "live-site",
    project: "qbs",
    category: "Consulting / professional services",
    tags: ["agency-peer", "warm-accent", "condensed-headings", "credibility-first"],
    notes:
      "The closest live peer to QBS's own positioning — a Chicago web design and digital marketing agency. Warm brick accent (#BF472D) instead of the default tech blue, condensed headings against a regular body face, and a 4px base unit that keeps the layout tighter than the usual 8px agency template.",
    guardrails: [
      "a warm accent can read more credible than default tech blue for services work",
      "pair a condensed heading face against a regular body face rather than one weight of one family",
    ],
    tokens: {
      colorScheme: "light",
      colors: {
        primary: "#BF472D",
        secondary: "#607382",
        accent: "#D85B41",
        background: "#FFFFFF",
        textPrimary: "#1A1A1A",
        link: "#D85B41",
      },
      fonts: [
        { family: "Proxima Nova", role: "body" },
        { family: "Proxima Nova Condensed", role: "heading" },
      ],
      fontSizes: { h1: "64px", h2: "56px", body: "15px" },
      spacing: { baseUnit: 4, borderRadius: "5px" },
      components: {
        input: { background: "#F9F9FA", textColor: "#1A1A1A", borderRadius: "5px" },
        buttonPrimary: { background: "#BF472D", textColor: "#FFFFFF", borderRadius: "5px" },
        buttonSecondary: { background: "#1A1A1A", textColor: "#FFFFFF", borderRadius: "5px" },
      },
      personality: {
        tone: "professional",
        energy: "medium",
        targetAudience: "businesses seeking web design and digital marketing services",
      },
      designSystem: { framework: "custom" },
      confidence: { overall: 0.925 },
    },
  },
];

const existing = await readAll();
const seen = new Set(existing.map((r) => r.sourceUrl));

let added = 0;
for (const seed of seeds) {
  if (seen.has(seed.sourceUrl)) {
    console.log(`skip (already present): ${seed.title}`);
    continue;
  }
  const ref = await addReference(seed);
  console.log(`added ${ref.id}  ${ref.title}`);
  added++;
}
console.log(`\n${added} added, ${seeds.length - added} skipped.`);
