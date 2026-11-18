#!/usr/bin/env python3
"""Scene-relative caption offsets for Videowright segments."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "tools"))

import build_segment_data as bsd  # noqa: E402

DURATIONS = {
    "per_segment": {"a": [10.0, 22.5], "b": [8.0, 15.0]},
    "voiceovers": {"a": "one two", "b": "three four"},
}
CAPTIONS = {
    "cues": [
        {"id": "a-0", "scene_id": "a", "cues": [{"start": 0.0, "end": 2.0, "text": "x"}]},
        {"id": "a-1", "scene_id": "a", "cues": [{"start": 0.5, "end": 3.0, "text": "y"}]},
        {"id": "b-0", "scene_id": "b", "cues": [{"start": 1.0, "end": 2.0, "text": "z"}]},
    ]
}


class BuildSegmentDataTest(unittest.TestCase):
    def test_second_chunk_cues_are_offset_by_the_first_advance(self) -> None:
        _, cues_ts = bsd.build(DURATIONS, CAPTIONS)
        data = json.loads(cues_ts.split("=", 1)[1].rsplit(";", 1)[0])
        self.assertEqual(data["a"][0]["start"], 0.0)
        self.assertEqual(data["a"][1]["start"], 10.5)
        self.assertEqual(data["a"][1]["end"], 13.0)
        self.assertEqual(data["b"][0]["start"], 1.0)

    def test_timing_exports_advances_and_voiceover(self) -> None:
        timing, _ = bsd.build(DURATIONS, CAPTIONS)
        self.assertIn('"a": [', timing)
        self.assertIn("22.5", timing)
        self.assertIn('"one two"', timing)

    def test_example_pipeline_outputs_are_consistent(self) -> None:
        root = KIT / "example"
        timing = (root / "timing.ts").read_text()
        captions = (root / "captions.ts").read_text()
        self.assertIn('import type { Cue } from "./segments/shared"', captions)
        for scene in ["why", "how", "proof"]:
            self.assertIn(f'"{scene}"', timing)
            self.assertIn(f'"{scene}"', captions)
            self.assertIn('"text"', captions)


if __name__ == "__main__":
    unittest.main()
