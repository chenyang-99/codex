# AI TOOLVERSE — 3D AI Concepts Gallery

An original artwork remix of [InstaLanding.ai's Conveyor Gallery](https://github.com/RayVelez27/instalanding.ai/tree/main/motion/conveyor-gallery).

Eight **fictional** AI product concepts on a continuous WebGL 1.0 conveyor. Scroll or swipe, use arrow keys or navigation buttons, and click or choose **EXPLORE** for concept details.

## Run locally

Open index.html in a modern browser, or serve the repository root:

    python3 -m http.server 5173

Then open http://localhost:5173/examples/ai-toolverse-demo/

No NPM build required. Google Fonts are optional, with system fallback fonts; WebGL unsupported devices show a standard grid.

## Implementation

- Kept original WebGL 3D shader geometry, inertial scroll, pointer/touch interactions and GPU fallback.
- Created 8 new Canvas 2D card designs and fictional AI concept identities; no product logos or third-party image downloads.
- Added responsive navigation, title/status display, accessible detail dialog and source credit.
- Original upstream source remains untouched in examples/instalanding-conveyor-gallery/.

## Verification status

- **Completed:** GitHub write/read-back checks and JavaScript syntax parse.
- **Not yet completed:** real browser WebGL rendering, pointer/wheel testing, 390px layout, WebGL fallback, and screen recording.
- Not deployed. No X publication is implied.

See LICENSE and ATTRIBUTION.md.