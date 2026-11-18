#!/usr/bin/env bash
# One-time setup for the video-explainer-kit.
# Installs local Kokoro-82M TTS + Whisper into a venv.
# Override the venv path with EXPLAINER_VENV (or EXPLAIN_VIDEO_VENV). Idempotent: safe to re-run.
set -euo pipefail

VENV="${EXPLAINER_VENV:-${EXPLAIN_VIDEO_VENV:-$HOME/.venvs/explain-video}}"

node -e 'const [maj, min] = process.versions.node.split(".").map(Number); if (maj < 22 || (maj === 22 && min < 18)) { console.error(`setup.sh: Node 22.18+ required, found ${process.versions.node}`); process.exit(1); }' || exit 1
command -v ffmpeg >/dev/null 2>&1 || echo "setup.sh: install ffmpeg (brew install ffmpeg / apt install ffmpeg)"
if [[ "$(uname -s)" == "Darwin" ]]; then
  command -v espeak-ng >/dev/null 2>&1 || echo "setup.sh: espeak-ng is an optional misaki fallback: brew install espeak-ng"
  [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] || echo "setup.sh: Chrome not found at /Applications/Google Chrome.app (needed to render)"
elif [[ "$(uname -s)" == "Linux" ]]; then
  command -v google-chrome >/dev/null 2>&1 || command -v chromium >/dev/null 2>&1 || echo "setup.sh: Chrome/Chromium not found (needed to render)"
fi

command -v uv >/dev/null 2>&1 || { echo "setup.sh: install uv first: https://docs.astral.sh/uv/"; exit 1; }
[ -x "$VENV/bin/python" ] || uv venv --python 3.12 "$VENV"

export VIRTUAL_ENV="$VENV"

# kokoro pins an old transformers/tokenizers with no macOS arm64 wheels.
# Install kokoro without deps, then a modern transformers instead.
uv pip install --no-deps kokoro
uv pip install loguru huggingface-hub numpy torch "misaki[en]" soundfile \
  "transformers>=4.40,<4.50" openai-whisper

"$VENV/bin/python" - <<'EOF'
from kokoro import KPipeline
import misaki
import whisper
KPipeline(lang_code="a")
print("Kokoro-82M weights cached. misaki and whisper import.")
EOF

echo "Setup complete."
echo "  venv:   $VENV"
echo "  voice:  af_heart (override with KOKORO_VOICE)"
