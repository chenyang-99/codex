# Anatomy Reveal Skill — official source checkout test

Source: https://github.com/annnguyentt/anatomy-reveal-skill
Upstream pinned commit: `dd01e1c04559d79002da07862e26f8a5c2a07644`.
Original MIT LICENSE and THIRD_PARTY_NOTICES.md are retained.

The directory `.agents/skills/anatomy-reveal` contains the 37 original, runnable
source, references, build scripts, template and license text files (copied byte-for-byte
as UTF-8). The three `demo/` binary files (two PNGs and one MP4) are omitted because
the GitHub connector permits text-only reads. These are NOT used by the scripts.
See the upstream repository for the original demonstration videos/images.

Run the GitHub Actions workflow `.github/workflows/anatomy-reveal-smoke.yml`.
It executes the original Skill's `scripts/new-project.mjs`, renders the
82-part espresso example's interactive HTML, checks parts and animation,
renders a 3-second 9:16 30fps low-blur-quality smoke MP4, verifies decoding,
and uploads generated outputs as Actions artifacts.

**Scope:** This is an official upstream example baseline run, **not** an
independent photo-to-3D reconstruction. The smoke film uses `--most 1` for
lower compute usage; the author's default cinematic motion blur uses more
samples. A passing result must not be misreported as a new-object AI test.

Running the workflow consumes GitHub Actions minutes and uses npm / apt
downloads but no paid AI models or external inference APIs.

Credits: Ann Nguyen, original MIT-licensed Anatomy Reveal project.
