#!/usr/bin/env python3
"""Repair coverage: token rewriting, chunk ownership, skipped chunks, caption merging."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "speech"))

import verify_audio as va  # noqa: E402


class RepairLineTest(unittest.TestCase):
    def test_wordy_token_is_letter_spelled(self) -> None:
        updated, tried = va._repair_line("onAfterChange happened", "onAfterChange happened", ["on", "change"])
        self.assertEqual(tried, ["onAfterChange"])
        self.assertEqual(updated, "O N A F T E R C H A N G E happened")

    def test_abbreviated_token_gets_phonemes(self) -> None:
        with patch.object(va, "_phonemes", return_value="ˌeɪ p i"):
            updated, tried = va._repair_line("Call the API now", "Call the API now", ["a", "p"])
        self.assertEqual(tried, ["API"])
        self.assertEqual(updated, "Call the [API](/ˌeɪ p i/) now")

    def test_matching_tokens_are_left_alone(self) -> None:
        updated, tried = va._repair_line("on after change happened", "onAfterChange happened", ["unrelated"])
        self.assertEqual(updated, "on after change happened")
        self.assertEqual(tried, [])

    def test_missing_phonemes_fall_back_to_tried_only(self) -> None:
        with patch.object(va, "_phonemes", return_value=""):
            updated, tried = va._repair_line("Call the API now", "Call the API now", ["a", "p"])
        self.assertEqual(updated, "Call the API now")
        self.assertEqual(tried, ["API"])


class ApplyRepairsTest(unittest.TestCase):
    def scenes(self, tmp: Path) -> Path:
        path = tmp / "scenes.json"
        path.write_text(
            json.dumps(
                {
                    "scenes": [
                        {
                            "id": "s",
                            "lines": [
                                {"display": "onAfterChange happened", "spoken": "onAfterChange happened"},
                                {"display": "second line", "spoken": "second line"},
                            ],
                        }
                    ]
                }
            )
        )
        return path

    def durations(self) -> dict:
        return {
            "chunks": [
                {"id": "c1", "scene_id": "s", "line_indexes": [0]},
                {"id": "c2", "scene_id": "s", "line_indexes": [0, 1]},
            ]
        }

    def test_single_line_chunks_are_repaired_and_owned_by_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.scenes(Path(tmp))
            tried_by_chunk, skipped = va._apply_repairs(
                path, [{"id": "c1", "scene_id": "s", "mismatched": ["on", "change"]}], self.durations()
            )
            self.assertEqual(tried_by_chunk, {"c1": ["onAfterChange"]})
            self.assertEqual(skipped, [])
            spoken = json.loads(path.read_text())["scenes"][0]["lines"][0]["spoken"]
            self.assertEqual(spoken, "O N A F T E R C H A N G E happened")

    def test_multi_line_chunks_are_reported_as_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.scenes(Path(tmp))
            tried_by_chunk, skipped = va._apply_repairs(
                path, [{"id": "c2", "scene_id": "s", "mismatched": ["second"]}], self.durations()
            )
            self.assertEqual(tried_by_chunk, {})
            self.assertEqual(skipped, ["c2"])
            self.assertEqual(json.loads(path.read_text())["scenes"][0]["lines"][1]["spoken"], "second line")


class MergeCaptionsTest(unittest.TestCase):
    def test_unchecked_chunks_keep_their_captions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.json"
            path.write_text(json.dumps({"cues": [{"id": "a", "cues": [{"start": 0.0, "end": 1.0, "text": "old a"}]}, {"id": "b", "cues": []}]}))
            merged = va._merge_captions(path, [{"id": "b", "cues": [{"start": 0.5, "end": 1.5, "text": "new b"}]}, {"id": "c", "cues": []}])
            self.assertEqual([cue["id"] for cue in merged], ["a", "b", "c"])
            self.assertEqual(merged[0]["cues"][0]["text"], "old a")
            self.assertEqual(merged[1]["cues"][0]["text"], "new b")

    def test_corrupt_or_missing_file_starts_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.json"
            self.assertEqual(va._merge_captions(path, [{"id": "a", "cues": []}]), [{"id": "a", "cues": []}])
            path.write_text("not json")
            self.assertEqual(va._merge_captions(path, [{"id": "a", "cues": []}]), [{"id": "a", "cues": []}])


class ClearedTokensTest(unittest.TestCase):
    def test_only_tokens_whose_chunk_is_clean_count_as_cleared(self) -> None:
        tried = {"c1": ["onAfterChange"], "c2": ["API"]}
        self.assertEqual(va._cleared_tokens(tried, {"c2"}), ["onAfterChange"])
        self.assertEqual(va._cleared_tokens(tried, set()), ["onAfterChange", "API"])
        self.assertEqual(va._cleared_tokens(tried, {"c1", "c2"}), [])


if __name__ == "__main__":
    unittest.main()
