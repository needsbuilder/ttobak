# Assets — pictograms (separately licensed, NOT Apache-2.0)

This directory ships pictogram glyphs under their own **CC BY-SA** licenses,
kept deliberately separate from the Apache-2.0 code in `ttobak/` (spec §9.4).

> Exception: [`brand/`](brand/README.md) holds the project's own logo/banner
> art and demo screenshots — those are Apache-2.0 project artifacts, placed
> here only because the separation gate keeps image binaries inside `assets/`.

```
assets/pictograms/
  mulberry/   (unmodified)  LICENSE = CC BY-SA 2.0 UK + ATTRIBUTION.md
  openmoji/   (unmodified)  LICENSE = CC BY-SA 4.0  + ATTRIBUTION.md
  derived/    (our edits)   LICENSE = CC BY-SA (matching source set) + CHANGES.md
```

## Rules (license-gate compliance)
- ShareAlike (SA) on these assets does NOT infect the Apache code — they are a
  separate work (mere aggregation).
- The renderer references pictograms **by file path / URL only**. It MUST NOT
  inline or base64-embed a *modified* CC BY-SA glyph into Apache code output or
  CC BY data output (avoids creating a combined work) — spec §9.4 embed rule.
- Modified glyphs (`derived/`) keep the same CC BY-SA license + CHANGES.md.

## Attribution
- Mulberry Symbols © 2018–2026 Steve Lee, CC BY-SA 2.0 UK — https://mulberrysymbols.org
- OpenMoji, CC BY-SA 4.0 — https://openmoji.org
