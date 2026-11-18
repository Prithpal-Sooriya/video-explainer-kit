#!/usr/bin/env python3
"""The renderer's layout check must catch overlap, overflow and low contrast, and pass clean kit scenes."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
VW = KIT / "render" / "vw.ts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "layout"
ME_CSS = KIT / "themes" / "motion-engineering" / "style.css"
ME_SHA = "c2f5f7e9daf7d11718f954c2f1afbe891e0204a12421ec6d2ee7565fff26d17b"


def check(timeline: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(VW), "render", timeline, "--check"], cwd=FIXTURE, capture_output=True, text=True, timeout=180
    )


def chrome_available() -> bool:
    probe = check("fixture.timeline.ts")
    return "layout check" in probe.stdout + probe.stderr


@unittest.skipUnless(shutil.which("node"), "node not installed")
class LayoutCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not chrome_available():
            raise unittest.SkipTest("Chrome not available")

    def test_bad_fixture_fails_with_every_defect(self) -> None:
        r = check("bad.timeline.ts")
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        expected = [
            r"bad-overlap beat 1/2: outside safe area: h1\[data-title\] .* top \d+ < 152",
            r"bad-overlap beat 1/2: covers chrome: h1\[data-title\] .* overlaps div\.vw-lockup",
            r"bad-overlap beat 1/2: overlap: div\.vw-card \"Before.* × div\.vw-card \"After.* by 140x220px",
            r"bad-bounds beat 1/1: outside safe area: div\.vw-pill \"tools/build_segment_data",
            r"bad-bounds beat 1/1: off canvas: div\.vw-pill \"tools/build_segment_data",
            r"bad-bounds beat 1/1: off canvas: img\[data-img\]",
            r"bad-bounds beat 1/1: clipped text: div\.vw-card \"Clipped",
            r"bad-contrast beat 1/1: low contrast: div\.vw-title \"What changed\" 1\.11:1 < 3:1 \(#000000 on #101014, 88px large\)",
            r"bad-contrast beat 1/1: low contrast: div\.vw-card-title \"Safe area\" 1\.06:1 < 3:1",
            r"bad-contrast beat 1/1: low contrast: div\.vw-body \"Grew from 0px to 96px\.\" 1\.41:1 < 3:1",
            r"bad-contrast beat 1/1: low contrast: div\.vw-body \"Now catches every spill\.\" 3\.16:1 < 4\.5:1",
            r"bad-contrast beat 1/1: low contrast: span\.vw-pill \"KIT-0001\" 2\.39:1 < 4\.5:1",
        ]
        for pattern in expected:
            self.assertRegex(out, pattern)
        self.assertNotRegex(out, r": (?:\w+ )+div\.vw-captions|: (?:\w+ )+div\.vw-lockup")
        self.assertRegex(out, r"Layout check failed with \d+ errors")

    def test_clean_fixtures_pass(self) -> None:
        for timeline in ["fixture", "tailwind"]:
            with self.subTest(timeline=timeline):
                r = check(f"{timeline}.timeline.ts")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("layout check: OK (5 beats in 4 segments)", r.stdout)

    def test_clean_fixtures_have_no_notes(self) -> None:
        for timeline in ["fixture", "tailwind", "me"]:
            with self.subTest(timeline=timeline):
                r = check(f"{timeline}.timeline.ts")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertNotIn("note ", r.stdout + r.stderr)

    def test_late_image_is_measured_after_it_settles(self) -> None:
        r = check("late-image.timeline.ts")
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        self.assertNotIn("low contrast", out)
        self.assertIn("layout check: OK (1 beat in 1 segment)", out)

    def test_notes_are_reported_and_do_not_fail(self) -> None:
        r = check("notes.timeline.ts")
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        expected = [
            r"note notes-tight beat 1/1: cards nearly touching \(8px gap\) -> use gap-6 or more",
            r"note notes-tight beat 1/1: text too close to its card's edge \(\d+px\) -> use p-6 or more \(on div\.text-heading-sm\.text-default \"After\"",
            r"note notes-sparse beat 1/1: large empty area \(content covers \d+% of the safe area\)",
            r"note notes-sparse beat 1/1: content bunched on the left \(\d+% of the width empty on the right\)",
            r"note notes-measure beat 1/1: lines too long to read \(~\d+ characters\)",
        ]
        for pattern in expected:
            self.assertRegex(out, pattern)
        self.assertNotRegex(out, r"note notes-tight .*\"Before\" in")
        summary = out.index("layout check: OK (3 beats in 3 segments)")
        self.assertLess(summary, out.index("note "))

    def test_unknown_classes_fail_with_a_fix(self) -> None:
        r = check("bad-tailwind.timeline.ts")
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        expected = [
            r"unknown-class: text-4xl -> use text-heading-lg",
            r"unknown-class: text-gray-500 -> the theme's tailwind\.css does not define palette colours; add them to its tokens\.json or use text-alternative",
            r"unknown-class: text-\[13px\] -> use a type role: text-body-md, text-heading-sm, text-display-md…",
            r"unknown-class: bg-\[#111\] -> use a colour class from the theme's tailwind\.css \(e\.g\. bg-section\)",
            r"unknown-class: text-white -> use text-default",
            r"unknown-class: text-error-muted -> error-muted is a fill, not readable as text; use bg-error-muted with text-default on it",
            r"unknown-class: gap-13 -> not on the scale; use gap-12",
            r"unknown-class: hover:bg-section -> use bg-section \(no variants: one static frame, dark only\)",
        ]
        for pattern in expected:
            self.assertRegex(out, pattern)
        self.assertEqual(out.count("unknown-class"), 8, out)

    def test_theme_decoration_is_painted_by_the_theme(self) -> None:
        for css in [FIXTURE / "styles" / "fixture" / "style.css", KIT / "themes" / "motion-engineering" / "tokens.css"]:
            with self.subTest(css=css.name):
                text = css.read_text()
                self.assertRegex(text, r"\.vw-stage::before \{[^}]*z-index: -1;[^}]*pointer-events: none;")
        for seg in (FIXTURE / "segments").glob("clean-*/index.ts"):
            self.assertNotIn("data-vw-decor", seg.read_text(), seg)

    def test_theme_sheet_is_a_module_and_stays_off_the_theme(self) -> None:
        sheet = (FIXTURE / "kit" / "tailwind.css").read_text()
        self.assertIn("--vw-tailwind: 1;", sheet)
        for css in [FIXTURE / "styles" / "fixture" / "style.css", KIT / "themes" / "motion-engineering" / "style.css"]:
            self.assertNotIn("--vw-tailwind", css.read_text(), css)
        kit_css = (FIXTURE / "kit" / "kit.css").read_text()
        sheet_classes = {line.split("{")[0].strip().lstrip(".") for line in sheet.splitlines() if line.startswith(".")}
        self.assertFalse([c for c in sheet_classes if c.startswith("vw-")], sheet_classes)
        self.assertIn(".vw-stage", kit_css)

    def test_clean_fixture_passes_motion_engineering(self) -> None:
        digest = subprocess.run(["shasum", "-a", "256", str(ME_CSS)], capture_output=True, text=True).stdout.split()[0]
        self.assertEqual(digest, ME_SHA)
        r = check("me.timeline.ts")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("layout check: OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
