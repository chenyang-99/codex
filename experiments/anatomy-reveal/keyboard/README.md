# 60% keyboard — independent new-product Anatomy Reveal test

Author's original engine lives under `.agents/skills/anatomy-reveal` and is unchanged.

This **new geometry** is written for a 61-key generic mechanical keyboard.
The test replaces the example-specific `geometry.mjs`, `film.mjs` and
`timeline.mjs` in a freshly scaffolded official Anatomy project. It still
uses the upstream Node/Chrome 3D projection, object interaction, collision
scanning, SVG renderer and H.264 video export.

Assumptions: keyboard roughly 290 x 106 x 32 mm; 61 individually labelled
keycaps, 61 simplified switch housings, mounting plate, PCB, case, feet and
USB connector. 3D layers are illustrative, not manufacturer-verified.
The mounting plate is a slab without real switch cutouts.

**Testing status must come from GitHub Actions logs and artifact.** The
workflow runs five camera-view collision scans and checks all frames, then
exports a vertically framed low-cost H.264 smoke movie (one sample per frame).
Report the actual duration/frames from ffprobe, not the requested value.

Important: this test is a **custom coded name-to-geometry test**, not AI
autonomously reconstructing an uploaded product photo. It does demonstrate
the *original Skill pipeline* working with a totally new product.
