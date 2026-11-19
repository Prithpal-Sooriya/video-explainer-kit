#!/usr/bin/env python3
"""Kokoro pipeline construction must match kokoro 0.9.4's real signatures."""

from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "speech"))

import synth  # noqa: E402

try:
    import huggingface_hub  # noqa: E402
except ImportError:
    huggingface_hub = None

try:
    import kokoro  # noqa: E402
except ImportError:
    kokoro = None


@unittest.skipIf(kokoro is None, "kokoro not installed")
class PipelineConstructionTest(unittest.TestCase):
    def setUp(self) -> None:
        synth._PIPELINE = None
        self.addCleanup(setattr, synth, "_PIPELINE", None)
        calls: list = []

        class KPipeline:
            def __init__(self, *args, **kwargs):
                inspect.signature(kokoro.KPipeline.__init__).bind(None, *args, **kwargs)
                calls.append(("pipeline", args, kwargs))

        class KModel:
            def __init__(self, *args, **kwargs):
                inspect.signature(kokoro.KModel.__init__).bind(None, *args, **kwargs)
                calls.append(("model", args, kwargs))

            def to(self, device):
                calls.append(("to", (), {"device": device}))
                return self

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
        to_calls = [c for c in self.calls if c[0] == "to"]
        self.assertEqual(len(to_calls), 1)
        self.assertIn(to_calls[0][2]["device"], ("cpu", "cuda"))

    def test_pinned_revision_is_downloaded(self) -> None:
        synth._pipeline()
        downloads = [c[2] for c in self.calls if c[0] == "download"]
        self.assertTrue(downloads)
        for kwargs in downloads:
            self.assertEqual(kwargs.get("repo_id"), synth.KOKORO_REPO)
            self.assertEqual(kwargs.get("revision"), synth.KOKORO_REVISION)


class VoiceResolutionTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(synth, "_hf_file", side_effect=lambda filename: f"/cache/{filename}")
        self.hf_file = patcher.start()
        self.addCleanup(patcher.stop)

    def test_voice_name_resolves_to_pinned_file(self) -> None:
        self.assertEqual(synth._voice("af_heart"), "/cache/voices/af_heart.pt")
        self.hf_file.assert_called_once_with("voices/af_heart.pt")

    def test_local_file_without_pt_suffix_still_resolves_via_hf(self) -> None:
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            self.addCleanup(os.chdir, cwd)
            Path("af_heart").touch()
            self.assertEqual(synth._voice("af_heart"), "/cache/voices/af_heart.pt")
        self.hf_file.assert_called_once_with("voices/af_heart.pt")

    def test_pt_path_passes_through(self) -> None:
        self.assertEqual(synth._voice("/tmp/af_heart.pt"), "/tmp/af_heart.pt")
        self.hf_file.assert_not_called()

    def test_comma_voices_resolve_separately(self) -> None:
        self.assertEqual(synth._voice("af_heart,af_bella"), "/cache/voices/af_heart.pt,/cache/voices/af_bella.pt")
        self.assertEqual(
            self.hf_file.call_args_list,
            [mock.call("voices/af_heart.pt"), mock.call("voices/af_bella.pt")],
        )


@unittest.skipIf(huggingface_hub is None, "huggingface_hub not installed")
class HfFileTest(unittest.TestCase):
    def test_hf_file_pins_repo_and_revision(self) -> None:
        with mock.patch.object(huggingface_hub, "hf_hub_download", return_value="/cache/f") as download:
            self.assertEqual(synth._hf_file("config.json"), "/cache/f")
        download.assert_called_once_with(
            repo_id=synth.KOKORO_REPO, filename="config.json", revision=synth.KOKORO_REVISION
        )


class KokoroPinTest(unittest.TestCase):
    def test_revision_is_pinned(self) -> None:
        self.assertEqual(synth.KOKORO_REPO, "hexgrad/Kokoro-82M")
        self.assertEqual(synth.KOKORO_REVISION, "f3ff3571791e39611d31c381e3a41a3af07b4987")
        self.assertEqual(synth.KOKORO_WEIGHTS, "kokoro-v1_0.pth")


if __name__ == "__main__":
    unittest.main()
