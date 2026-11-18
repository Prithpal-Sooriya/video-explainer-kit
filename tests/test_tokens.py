#!/usr/bin/env python3
"""The theme tokens pipeline: snapshot format, tailwind generation, drift checks, theme contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "layout"
sys.path.insert(0, str(KIT / "tools"))

import tailwind  # noqa: E402
import tokens  # noqa: E402

FIXTURE_SNAP = json.loads((FIXTURE / "styles" / "fixture" / "tokens.json").read_text())
ME_SNAP = json.loads((KIT / "themes" / "motion-engineering" / "tokens.json").read_text())


class ClassSet(unittest.TestCase):
    def test_fixture_vocabulary_is_present(self) -> None:
        names = set(tailwind.class_names(FIXTURE_SNAP))
        for c in [
            "text-default",
            "text-alternative",
            "text-error-default",
            "text-success-default",
            "text-warning-default",
            "text-primary-default",
            "text-primary-inverse",
            "bg-primary-default",
            "bg-error-muted",
            "bg-success-muted",
            "border-default",
            "border-muted",
            "border-accent-default",
            "fill-accent-default",
            "stroke-accent-default",
            "text-display-lg",
            "text-body-xs-medium",
            "gap-8",
            "p-10",
            "rounded-md",
            "flex",
            "grid-cols-3",
            "col-span-2",
            "self-start",
            "line-through",
            "font-mono",
        ]:
            self.assertIn(c, names, c)

    def test_unreadable_text_is_not_offered(self) -> None:
        names = set(tailwind.class_names(FIXTURE_SNAP))
        for c in ["text-error-muted", "text-primary-default-what"]:
            self.assertNotIn(c, names, c)

    def test_default_theme_ships_a_stock_palette(self) -> None:
        names = set(tailwind.class_names(ME_SNAP))
        for c in ["text-accent-default", "text-measure-default", "text-cyan-300", "text-cyan-500", "bg-slate-950", "bg-slate-900", "border-slate-700"]:
            self.assertIn(c, names, c)
        self.assertNotIn("text-slate-500", names, "slate-500 text fails AA on the ME surfaces")

    def test_contrast_math(self) -> None:
        self.assertAlmostEqual(tailwind.contrast("#ffffff", "#000000"), 21, places=1)
        self.assertAlmostEqual(tailwind.contrast("#000000", "#ffffff"), 21, places=1)
        self.assertGreater(tailwind.contrast("#ff8800", "#101014"), 4.5)

    def test_generated_sheets_are_committed_in_sync(self) -> None:
        for snap_path, sheet in [
            (KIT / "themes" / "motion-engineering" / "tokens.json", KIT / "themes" / "motion-engineering" / "tailwind.css"),
            (FIXTURE / "styles" / "fixture" / "tokens.json", FIXTURE / "kit" / "tailwind.css"),
        ]:
            with self.subTest(sheet=sheet.name):
                snap = json.loads(snap_path.read_text())
                self.assertEqual(tailwind.generate(snap), sheet.read_text())

    def test_drift_check_detects_a_stale_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            theme = Path(tmp) / "theme"
            theme.mkdir()
            snap = json.loads((FIXTURE / "styles" / "fixture" / "tokens.json").read_text())
            snap["colors"]["text-default"] = "#ffffff"
            (theme / "tokens.json").write_text(json.dumps(snap))
            sheet = theme / "tailwind.css"
            sheet.write_text(tailwind.generate(json.loads((FIXTURE / "styles" / "fixture" / "tokens.json").read_text())))
            self.assertEqual(tokens.build(str(theme), None, True), 1)
            self.assertEqual(tokens.build(str(theme), None, False), 0)
            self.assertEqual(tokens.build(str(theme), None, True), 0)


class ImportCss(unittest.TestCase):
    CSS = """
.dark {
  --color-bg-default: #0e141a;
  --color-fg-default: var(--color-bg-default);
  --color-bg-section: #131c25;
  --color-border-default: var(--color-bg-default);
  --color-accent-default: #ff8800;
  --color-text-default: #e8eef5;
  --typography-display-md-font-size: 64px;
  --typography-display-md-line-height: 68px;
  --typography-display-md-font-weight: 500;
  --typography-display-md-letter-spacing: -0.01em;
  --typography-body-md-font-size: 20px;
  --typography-body-md-line-height: 28px;
  --typography-body-md-letter-spacing: 0em;
  --typography-body-md-font-weight: 400;
}
"""

    def test_import_writes_a_scaled_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            css = root / "design-tokens.css"
            css.write_text(self.CSS)
            out = root / "tokens.json"
            r = subprocess.run(
                [sys.executable, str(KIT / "tools" / "tokens.py"), "import", "--from", str(css), "--name", "acme", "--version", "2.0", "--scale", "1.75", "--out", str(out)],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            snap = json.loads(out.read_text())
            self.assertEqual((snap["name"], snap["version"], snap["scale"]), ("acme", "2.0", 1), "import bakes the scale in and stores 1")
            self.assertEqual(snap["colors"]["bg-default"], "#0e141a")
            self.assertEqual(snap["colors"]["fg-default"], "#0e141a", "var() chains resolve")
            self.assertEqual(snap["colors"]["border-default"], "#0e141a", "cross-block var() resolves")
            self.assertEqual(snap["type"]["display-md"]["font-size"], 112, "scale multiplies")
            self.assertEqual(snap["type"]["body-md"]["font-size"], 35)
            self.assertEqual(snap["type"]["display-md"]["font-weight"], 500)

    def test_imported_snapshot_builds_a_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "design-tokens.css").write_text(self.CSS)
            snap_path = root / "tokens.json"
            subprocess.run(
                [sys.executable, str(KIT / "tools" / "tokens.py"), "import", "--from", str(root / "design-tokens.css"), "--name", "acme", "--out", str(snap_path)],
                capture_output=True, text=True, check=True,
            )
            snap = json.loads(snap_path.read_text())
            names = set(tailwind.class_names(snap))
            self.assertIn("bg-default", names)
            self.assertIn("text-default", names)
            self.assertIn("border-default", names)
            self.assertIn("text-display-md", names)


class ThemeContract(unittest.TestCase):
    def test_builtin_theme_files(self) -> None:
        theme = KIT / "themes" / "motion-engineering"
        self.assertTrue((theme / "style.css").is_file())
        self.assertTrue((theme / "STYLE.md").is_file())
        self.assertTrue((theme / "tokens.json").is_file())
        self.assertTrue((theme / "tailwind.css").is_file())
        self.assertTrue((theme / "tokens.css").is_file())

    def test_theme_names_resolve(self) -> None:
        self.assertEqual(tokens.theme_dir("motion-engineering"), (KIT / "themes" / "motion-engineering").resolve())
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(tokens.theme_dir(str(Path(tmp).resolve())), Path(tmp).resolve())
        with self.assertRaises(SystemExit):
            tokens.theme_dir("no-such-theme")

    def test_theme_init_scaffolds_a_working_theme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            theme = Path(tmp) / "acme"
            r = subprocess.run(["node", str(KIT / "bin" / "explainer"), "theme", "init", "acme", str(theme)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ["style.css", "STYLE.md", "tokens.json", "tailwind.css"]:
                self.assertTrue((theme / f).is_file(), f)
            sheet = (theme / "tailwind.css").read_text()
            self.assertIn("--vw-tailwind: 1;", sheet)
            self.assertIn(".bg-accent-default", sheet)
            self.assertIn(".text-default", sheet)
            snap = json.loads((theme / "tokens.json").read_text())
            self.assertEqual(snap["name"], "acme")
            self.assertEqual(tokens.build(str(theme), None, True), 0)


if __name__ == "__main__":
    unittest.main()
