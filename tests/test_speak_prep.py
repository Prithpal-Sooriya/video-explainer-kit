#!/usr/bin/env python3
"""Normalizer coverage for the explainer pronunciation pipeline, incl. theme lexicon layering."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "speech"))

import speak_prep as sp  # noqa: E402
import verify_audio as va  # noqa: E402


LEXICON = sp.load_lexicon()


class SpeakPrepTest(unittest.TestCase):
    def test_on_after_change(self) -> None:
        self.assertEqual(sp.normalize_spoken("onAfterChange", {}), "on after change")

    def test_get_user_info(self) -> None:
        self.assertEqual(sp.normalize_spoken("getUserInfo", {}), "get user info")

    def test_http_server(self) -> None:
        self.assertEqual(sp.normalize_spoken("HTTPServer", {}), "H T T P server")

    def test_snake_case(self) -> None:
        self.assertEqual(sp.normalize_spoken("snake_case_name", {}), "snake case name")

    def test_api(self) -> None:
        self.assertEqual(sp.normalize_spoken("API", {}), "A P I")

    def test_ts_extension(self) -> None:
        self.assertEqual(sp.normalize_spoken(".ts", {}), "dot T S")

    def test_equals(self) -> None:
        self.assertEqual(sp.normalize_spoken("==", {}), "equals equals")

    def test_sentence(self) -> None:
        raw = "onAfterChange in HTTPServer.ts"
        expected = "on after change in H T T P server dot T S"
        self.assertEqual(sp.normalize_spoken(raw, {}), expected)

    def test_lexicon_override(self) -> None:
        custom = {"API": {"spoken": "ay pee eye"}}
        self.assertEqual(sp.normalize_spoken("Use the API now", custom), "Use the ay pee eye now")
        self.assertEqual(sp.normalize_spoken("API", LEXICON), "A P I")
        self.assertEqual(sp.normalize_spoken(".json", {}), "dot J S O N", "extensions are built in")
        self.assertEqual(sp.normalize_spoken("Kokoro", LEXICON), "ko ko ro")
        self.assertEqual(sp.normalize_spoken("FFmpeg", LEXICON), "F F mpeg")

    def test_theme_lexicon_layers_over_the_kit_default(self) -> None:
        scenes = {"scenes": [{"id": "one", "lines": [{"display": "Run the CLI and the API.", "spoken": "Run the CLI and the API."}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenes_path = root / "scenes.json"
            scenes_path.write_text(json.dumps(scenes))
            theme = root / "theme"
            theme.mkdir()
            (theme / "lexicon.json").write_text(json.dumps({"CLI": {"spoken": "command line interface"}}))
            self.assertEqual(sp.main([str(scenes_path), "--theme", str(theme)]), 0)
            data = json.loads(scenes_path.read_text())
            spoken = data["scenes"][0]["lines"][0]["spoken"]
            self.assertIn("command line interface", spoken)
            self.assertIn("A P I", spoken)

    def test_id_is_abbreviation(self) -> None:
        marked = "[id](/ˌIˈdi/)"
        self.assertEqual(sp.normalize_spoken("id", LEXICON), marked)
        self.assertEqual(sp.normalize_spoken("ID", LEXICON), "[ID](/ˌIˈdi/)")
        self.assertEqual(sp.normalize_spoken("userId", LEXICON), f"user {marked}")
        self.assertEqual(sp.normalize_spoken("chain_id", LEXICON), f"chain {marked}")
        self.assertEqual(sp.normalize_spoken("valid identity", LEXICON), "valid identity")
        self.assertEqual(sp.normalize_spoken("I'd rather", LEXICON), "I'd rather")
        self.assertEqual(sp.normalize_spoken(marked, LEXICON), marked)

    def test_phoneme_override(self) -> None:
        custom = {"API": {"spoken": "A P I", "phonemes": "ˌeɪ p i"}}
        marked = "[API](/ˌeɪ p i/)"
        self.assertEqual(sp.normalize_spoken("API", custom), marked)
        self.assertEqual(sp.normalize_spoken(marked, custom), marked)

    def test_idempotence(self) -> None:
        samples = [
            "onAfterChange",
            "getUserInfo",
            "HTTPServer",
            "snake_case_name",
            "API",
            ".ts",
            "==",
            "onAfterChange in HTTPServer.ts",
            "Run the CLI beside FFmpeg and Kokoro",
            "userId",
            "the id",
        ]
        for sample in samples:
            once = sp.normalize_spoken(sample, LEXICON)
            twice = sp.normalize_spoken(once, LEXICON)
            self.assertEqual(once, twice, sample)

    def test_scenes_file_idempotence(self) -> None:
        scenes = {
            "scenes": [
                {
                    "id": "one",
                    "lines": [
                        {
                            "display": "onAfterChange in HTTPServer.ts",
                            "spoken": "onAfterChange in HTTPServer.ts",
                        }
                    ],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenes.json"
            path.write_text(json.dumps(scenes), encoding="utf-8")
            self.assertEqual(sp.main([str(path)]), 0)
            first = path.read_text(encoding="utf-8")
            self.assertEqual(sp.main([str(path)]), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), first)
            data = json.loads(first)
            self.assertEqual(
                data["scenes"][0]["lines"][0]["spoken"],
                "on after change in H T T P server dot T S",
            )

    def test_unknowns_skip_lexicon_and_english(self) -> None:
        scenes = {
            "scenes": [
                {
                    "id": "one",
                    "lines": [
                        {"display": "onAfterChange API Kokoro the", "spoken": ""},
                        {"display": "onAfterChange", "spoken": ""},
                    ],
                }
            ]
        }
        rows = sp.collect_unknowns(scenes, LEXICON)
        tokens = [row["token"] for row in rows]
        self.assertEqual(tokens, ["onAfterChange"], "API is in the kit lexicon; Kokoro too; 'the' is common English")
        self.assertEqual(rows[0]["count"], 2)
        self.assertEqual(rows[0]["spoken"], "on after change")

    def test_whisper_autocorrect_matches_spoken(self) -> None:
        expected = "on after change in H T T P server dot T S"
        heard = "on Afterchange in HTTP Server.ts"
        self.assertEqual(va.mismatched_tokens(expected, heard), [])


if __name__ == "__main__":
    unittest.main()
