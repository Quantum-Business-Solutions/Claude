# Working generation prompts

Prompts that produced usable assets, kept verbatim so they're re-runnable and tunable rather than
re-derived from scratch. Record the model and the settings — a prompt without them isn't reusable.

---

## Isometric modular ring — dark + gold render

- **model:** `nano_banana_pro` (Higgsfield; resolves to `nano_banana_2`)
- **settings:** `aspect_ratio: "16:9"`, `resolution: "1k"`, `count: 4`
- **cost:** 2 credits per image at 1k (video on `seedance_2_0` is 22.5 — preflight with `get_cost: true`)
- **reference:** the technique entry in `references.md`
- **outcome:** 4/4 usable on the first run. Cleared the bar that two hand-coded attempts (flat SVG,
  then a raymarched SDF) both missed — see the medium guardrail in `guardrails.md`.

```
Premium 3D product render, elevated three-quarter near-isometric view. Six chunky modular blocks
with softly rounded bevelled edges arranged in a closed hexagonal ring, interlocking so their sides
touch, surrounding one single taller block at the exact centre. The six ring blocks are matte dark
navy-black anodised metal, colour #101725, very low reflectivity, subtle fine micro-texture. The
centre block is polished brushed gold, colour #C4A44A, clearly taller than the ring blocks, catching
a warm specular highlight along its top bevel edge. Deep near-black background colour #080B12 with
soft radial falloff, no horizon line, no floor pattern. Lighting: large soft softbox key from upper
left, cool subtle rim light from behind, gentle realistic contact shadows and ambient occlusion in
the narrow gaps where the blocks meet. Redshift / Octane render quality, crisp bevel highlights,
physically accurate materials, studio product photography, extremely clean and premium, 8k detail.
IMPORTANT: every surface is completely blank and empty — absolutely no text, no letters, no numbers,
no words, no logos, no labels, no icons, no symbols, no engravings on any face.
```

### What makes it work

- **Name the material, not the look.** "Matte dark navy-black anodised metal, very low reflectivity"
  beats "premium dark blocks." Same for "polished brushed gold" — that's what produced real
  anisotropic streaking instead of flat yellow.
- **Specify the light rig explicitly.** Softbox key direction, rim light, contact shadows, ambient
  occlusion. This is the single biggest lever; without it you get flat studio nothing.
- **Name a renderer.** "Redshift / Octane render quality" reliably shifts output toward physically
  plausible materials.
- **Demand blank faces, emphatically and last.** Text is where image models fail hardest, and this
  concept depends on legible service names. Generating blank and compositing labels afterward in
  Figma or Canva keeps type crisp, editable, translatable, and readable by search engines. The long
  "no text, no letters, no numbers…" clause is doing real work — shorten it and lettering creeps back.
- **Hex codes land approximately.** Treat them as direction, not spec. Grade to exact brand values in
  post if the asset has to match a live page.

### Known deviations

The model produced 8 ring blocks rather than the 6 requested, and read "hexagonal ring" loosely.
Composition is good regardless, but exact counts and arrangements aren't reliable — art-direct by
choosing among generations rather than by tightening the count in the prompt.
