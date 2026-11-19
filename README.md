# video-explainer-kit

Turn a technical change, doc, or spec into a short narrated explainer video — script, voice, and layout checks included — rendered locally with your own machine's tools. No cloud, no accounts: Node, Chrome, ffmpeg, and a local voice model do all the work.

Built for engineers, PMs, EMs, designers, and leaders who need to explain work that resists a slide deck: a PR that touches twenty files, a migration plan, an architecture decision record.

- **Natural narration** — one style: plain spoken English, no marketing voice.
- **One CLI** — `bin/explainer` runs the whole pipeline: prep, synth, verify, render.
- **Facts are checked** — every number you show must trace to a source you name before the video builds.
- **Layout is checked** — overlapping titles, clipped cards, unreadable grey text and off-screen beats fail the build, not the review.
- **Themes** — bring your design tokens, get Tailwind-shaped classes that the layout checker can lint. Ships with a dark, restrained "Motion Engineering" theme.

The renderer is [Videowright](https://github.com/scosman/videowright) (MIT) — DOM + CSS, screenshotted by Chrome, stitched by ffmpeg — carried in this repo with attribution (see `NOTICE`).

## What you get

```
video-explainer-kit/
├── bin/explainer        the CLI (setup, prep, synth, verify-audio, audition, segments, facts, tokens, render, theme)
├── render/              vw.ts renderer + layout-check.js (per-beat PNG inspection, contrast, bounds)
├── kit/                 shared segment helpers (kit.ts) + stage CSS (kit.css)
├── speech/              speak_prep (script normalization), synth (Kokoro), verify_audio (Whisper), audition
├── tools/               build_segment_data (timing + captions), verify_facts, tokens, tailwind
├── themes/motion-engineering/   built-in theme (style.css, tokens, Tailwind sheet, STYLE.md)
├── example/             a complete project that renders end-to-end with narration
├── lexicon.json         base pronunciation lexicon (API, FFmpeg, CLI, id, …)
├── setup.sh             installs the speech stack into a local venv
└── scripts/release.sh   builds the release tarball + sha256 (maintainers)
```

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Node | 22.18+ | CLI, renderer, segment authoring (runs TypeScript directly) |
| Chrome / Chromium | any recent | screenshots the DOM frames |
| ffmpeg | any recent | stitches frames + narration into mp4 |
| uv + Python 3.12 | uv 0.4+ | speech stack (Kokoro TTS + Whisper verification) |

Install the kit itself:

```bash
VERSION=0.1.0
curl -LO https://github.com/Prithpal-Sooriya/video-explainer-kit/releases/download/v${VERSION}/video-explainer-kit-${VERSION}.tar.gz
curl -LO https://github.com/Prithpal-Sooriya/video-explainer-kit/releases/download/v${VERSION}/video-explainer-kit-${VERSION}.tar.gz.sha256
shasum -a 256 -c video-explainer-kit-${VERSION}.tar.gz.sha256
mkdir -p ~/.cache/video-explainer-kit
tar -xzf video-explainer-kit-${VERSION}.tar.gz -C ~/.cache/video-explainer-kit
export PATH="$HOME/.cache/video-explainer-kit/video-explainer-kit-${VERSION}/bin:$PATH"
```

The `.sha256` sidecar guards against corrupted and stale downloads. It is served from the same release page as the tarball, so it is not tamper-proof on its own — compare it against the digest in the release notes if that matters to you.

Or clone this repo and use `bin/explainer` in place. The CLI is a single Bash script; nothing is installed globally.

## Setup (once per machine)

```bash
explainer setup          # checks Node/Chrome/ffmpeg, builds the speech venv (~/.venvs/explain-video)
```

The speech stack downloads Kokoro (voice) and Whisper (verification) models on first use — a few hundred MB, cached locally. Rendering and layout checks work without it.

## Make a video

A *project* is a directory with `scenes.json` (what you say), `facts.json` (what you must be able to prove), segment components (what you show), and a timeline. See `example/` for a complete one.

`scenes.json` speaks with Kokoro's `af_heart` voice by default; set `"voice": "af_sky"` (or any other Kokoro voice) and `"speed": 1.1` at the top level to change it for the whole project.

```bash
cd my-project

explainer prep scenes.json                 # normalize the script; prints unknown pronunciations
explainer facts scenes.json --facts facts.json --also segments/*/index.ts
explainer synth scenes.json                # Kokoro narration → audio/tracks/v1/track.{wav,mp3}
explainer verify-audio scenes.json         # Whisper re-listens; mismatches fail the build
explainer segments .                       # timing.ts + captions.ts from durations + captions
explainer render example.timeline.ts --check   # layout check; fails on overlap/contrast/bounds
explainer render example.timeline.ts       # mp4 with narration
```

Iterate on narration without re-synthesizing:

```bash
explainer audition scenes.json             # hear every line through the actual voice
```

## Rendering

`explainer render` passes through to the Videowright renderer:

```bash
explainer render TIMELINE.ts [--dry-run] [--check] [--frames DIR] [--output FILE.mp4]
                              [--fps N] [--size WxH] [--keep-open]
```

- `--dry-run` — validate the timeline and report the frame count; renders nothing.
- `--check` — screenshot every beat and run the layout check: contrast (AA), element bounds, clipping, unknown Tailwind classes, large empty areas. Zero errors required.
- `--frames DIR` — write one PNG per beat (`01-segment-beat.png`) for quick inspection.
- `--output` — final mp4 (h264 + aac). Missing narration renders silent with a warning, so `--check` works in CI without committed audio.

## Facts ledger

Every number, date, and named claim on screen or in speech must appear in `facts.json`:

```json
{
  "facts": [
    { "id": "F1", "shown": "1,426", "kind": "verbatim", "source": "render --dry-run, 2026-01-04" },
    { "id": "F2", "shown": "41.25", "kind": "derived", "source": "budget", "derivation": "28.5 + 12.75" }
  ],
  "allow": ["3"],
  "discrepancies": []
}
```

`verbatim` needs a source, `derived` needs a derivation, `external` needs attribution, unresolved discrepancies fail, unused facts warn. Small integers (counts) can be allow-listed.

## Themes

A theme is a directory with:

| File | Required | Purpose |
| --- | --- | --- |
| `style.css` | yes | theme CSS: fonts, surfaces, decorative elements, `--vw-*` variables |
| `STYLE.md` | yes | the theme's design rules, for the human writing segments |
| `tokens.json` | no | design tokens snapshot → generates `tailwind.css` |
| `lexicon.json` | no | brand pronunciations, layered over the kit lexicon (theme wins) |
| `tailwind.css` | generated | Tailwind-shaped classes, lintable by `--check` |

Use a built-in theme by name (`motion-engineering`) or any directory with `--theme <dir>`.

Bring your own design system: export a design-tokens CSS file (`--color-*`, `--typography-*`), import it, and build the class sheet. `--from` takes a plain `.css` file, a design-tokens package directory (`dist/styles.css`, `package/dist/styles.css`, or `src/css/{brand-colors,dark-theme-colors,typography}.css`), or such a package as a `.tgz`:

```bash
explainer tokens import --from design-tokens.css --name acme --version 2.0 --out themes/acme/tokens.json
explainer tokens build --theme themes/acme           # writes themes/acme/tailwind.css
explainer tokens build --theme themes/acme --check   # CI: fail if the sheet is stale
```

Colors become `text-*` / `bg-*` / `border-*` / `fill-*` / `stroke-*` classes (text classes must pass AA contrast against `bg-default`; `-inverse` pairs are exempt). Type roles become `text-display-lg`, `text-body-sm`, and so on, scaled for 1920×1080. Start a new theme from the scaffold:

```bash
explainer theme init acme themes/acme
```

The default snapshot (when a theme has no `tokens.json`) is the stock Tailwind v3.4 palette and spacing plus a generic type scale.

## CI

`.github/workflows/ci.yml` runs everything that needs no speech stack: python + node unit tests, the branding guard (this repo is unbranded; the guard greps for the old name), the example project's `--dry-run`, `--check`, and the tokens drift check. Use the same commands locally:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/test.ts
node bin/explainer render example/example.timeline.ts --check
```

## Releasing (maintainers)

```bash
scripts/release.sh 0.1.0       # builds tarball + .sha256 into dist/; does NOT tag or publish
git tag v0.1.0 && git push origin v0.1.0   # when ready
gh release create v0.1.0 dist/video-explainer-kit-0.1.0.tar.gz dist/video-explainer-kit-0.1.0.tar.gz.sha256
```

## License

MIT — see `LICENSE`. Attribution for carried and runtime dependencies in `NOTICE`.
