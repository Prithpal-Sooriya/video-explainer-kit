#!/usr/bin/env python3
"""Kokoro pipeline construction must match kokoro 0.9.4's real signatures."""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "speech"))

import synth  # noqa: E402

try:
    import huggingface_hub  # noqa: E402
    import kokoro  # noqa: E402
except ImportError:
    kokoro = None


@unittest.skipIf(kokoro is None, "kokoro not installed")
class PipelineConstructionTest(unittest.TestCase):
    def setUp(self) -> None:
        synth._PIPELINE = None
        calls: list = []

        class KPipeline:
            def __init__(self, *args, **kwargs):
                inspect.signature(kokoro.KPipeline.__init__).bind(None, *args, **kwargs)
                calls.append(("pipeline", args, kwargs))

        class KModel:
            MODEL_NAMES = kokoro.KModel.MODEL_NAMES

            def __init__(self, *args, **kwargs):
                inspect.signature(kokoro.KModel.__init__).bind(None, *args, **kwargs)
                calls.append(("model", args, kwargs))

            def eval(self):
                return self

        def hf_hub_download(**kwargs):
            calls.append(("download", (), kwargs))
            return f"/cache/{kwargs.get('filename')}"

        self.calls = calls
        patches = [
            mock.patch.object(kokoro, "KPipeline", KPipeline),
            mock.patch.object(kokoro, "KModel", KModel),
            mock.patch.object(huggingface_hub, "hf_hub_download", hf_hub_download),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_pipeline_kwargs_match_kokoro_signature(self) -> None:
        synth._pipeline()
        pipeline_calls = [c for c in self.calls if c[0] == "pipeline"]
        self.assertEqual(len(pipeline_calls), 1)
        self.assertEqual(pipeline_calls[0][2], {"lang_code": "a", "repo_id": synth.KOKORO_REPO, "model": mock.ANY})
        model_calls = [c for c in self.calls if c[0] == "model"]
        self.assertEqual(len(model_calls), 1)
        self.assertEqual(model_calls[0][2]["repo_id"], synth.KOKORO_REPO)

    def test_pinned_revision_is_downloaded(self) -> None:
        synth._pipeline()
        downloads = [c[2] for c in self.calls if c[0] == "download"]
        self.assertTrue(downloads)
        for kwargs in downloads:
            self.assertEqual(kwargs.get("repo_id"), synth.KOKORO_REPO)
            self.assertEqual(kwargs.get("revision"), synth.KOKORO_REVISION)

    def test_voice_resolves_to_pinned_file(self) -> None:
        resolved = synth._voice("af_heart")
        self.assertEqual(resolved, "/cache/voices/af_heart.pt")
        downloads = [c[2] for c in self.calls if c[0] == "download"]
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]["filename"], "voices/af_heart.pt")
        self.assertEqual(downloads[0]["revision"], synth.KOKORO_REVISION)

    def test_voice_path_passes_through(self) -> None:
        self.assertEqual(synth._voice("/tmp/af_heart.pt"), "/tmp/af_heart.pt")
        self.assertEqual(self.calls, [])


class KokoroPinTest(unittest.TestCase):
    def test_revision_is_pinned(self) -> None:
        self.assertEqual(synth.KOKORO_REPO, "hexgrad/Kokoro-82M")
        self.assertEqual(synth.KOKORO_REVISION, "f3ff3571791e39611d31c381e3a41a3af07b4987")


if __name__ == "__main__":
    unittest.main()
