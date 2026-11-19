#!/usr/bin/env python3
"""Build or import a theme's token snapshot (tokens.json) and generate its tailwind.css.

Stdlib only. Two steps, each runnable alone:

  build    read a theme's tokens.json and write (or check) the tailwind.css utility sheet
           --theme NAME|DIR   a built-in theme name (default: motion-engineering) or a
                              theme directory containing tokens.json
           --out FILE         where to write the sheet (default: the theme's tailwind.css)
           --check            exit 1 if the file differs from what the snapshot generates

  import   read a design-tokens CSS source and write a tokens.json snapshot for build
           --from PATH        one of: a plain .css file; a design-tokens package directory
                              (dist/styles.css, package/dist/styles.css, or
                              src/css/{brand-colors,dark-theme-colors,typography}.css);
                              or such a package as a .tgz
           --name NAME        the snapshot name (default: the source package name)
           --scale N          rem-to-px multiplier for the video canvas (default: 1.75)

The snapshot format (tokens.json) is the theme contract's colour and type layer:

  { "name": "my-theme", "version": "1.0.0", "scale": 1,
    "colors": { "bg-default": "#0e141a", "text-default": "#e8eef5", "primary-default": "#ff8800" },
    "type":   { "body-md": { "font-size": 28, "line-height": 39, "font-weight": 400, "letter-spacing": 0 } } }

Token names become classes: bg-*/background-* tokens are bg- utilities, text-*/fg-* are
text utilities, border-* are border utilities, and every other token gets all of
text-*/bg-*/border-*/fill-*/stroke-. Type roles become text-<role> classes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import tailwind

KIT = Path(__file__).resolve().parents[1]
DEFAULT_THEME = "motion-engineering"
IMPORT_SCALE = 1.75
REM = 16
SKIP = re.compile(r"-(hover|pressed)$")
TYPE_DECL = re.compile(r"--typography-(?:[lms]-)?([\w-]+?)-(font-size|line-height|font-weight|letter-spacing)$")

DECL = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)


def theme_dir(name: str) -> Path:
    path = Path(name)
    if path.is_dir():
        return path.resolve()
    built = KIT / "themes" / name
    if built.is_dir():
        return built
    raise SystemExit(f"unknown theme: {name} (not a directory and not a built-in theme under themes/)")


def snapshot_path(name: str) -> Path:
    path = theme_dir(name) / "tokens.json"
    if not path.exists():
        raise SystemExit(f"theme has no tokens.json: {path}")
    return path


def build(theme: str, out: Path | None, check: bool) -> int:
    snap = json.loads(snapshot_path(theme).read_text())
    sheet = tailwind.generate(snap)
    out = out or theme_dir(theme) / "tailwind.css"
    if check:
        if out.exists() and out.read_text() == sheet:
            print(f"tailwind.css: in sync with {snap['name']}@{snap['version']}")
            return 0
        print(f"drift: {out}")
        print(f"run: explainer tokens build --theme {theme} --out {out}")
        return 1
    out.write_text(sheet)
    print(f"wrote {out} ({len(tailwind.class_names(snap))} classes, {snap['name']}@{snap['version']})")
    return 0


def blocks(css: str) -> list[tuple[str, dict[str, str]]]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(sel.strip(), dict(DECL.findall(body + ";"))) for sel, body in BLOCK.findall(css)]


def read_source(path: Path) -> str:
    if path.is_file() and path.suffix == ".tgz":
        with tarfile.open(path) as tar:
            try:
                member = tar.extractfile("package/dist/styles.css")
            except KeyError:
                member = None
            if member is None:
                raise SystemExit(f"{path} has no package/dist/styles.css; not a design-tokens package tarball")
            return member.read().decode()
    if path.is_file():
        return path.read_text()
    for rel in ["dist/styles.css", "package/dist/styles.css"]:
        if (path / rel).exists():
            return (path / rel).read_text()
    src = path / "src" / "css"
    names = ["brand-colors.css", "dark-theme-colors.css", "typography.css"]
    if all((src / n).exists() for n in names):
        return "\n".join((src / n).read_text() for n in names)
    raise SystemExit(
        f"no design-tokens CSS under {path}: expected dist/styles.css, package/dist/styles.css, "
        f"or src/css/{'+'.join(n.removesuffix('.css') for n in names)}.css"
    )


def resolve(value: str, scope: dict[str, str]) -> str:
    for _ in range(10):
        m = re.fullmatch(r"\s*var\((--[\w-]+)\)\s*", value)
        if not m:
            return value.strip()
        value = scope[m.group(1)]
    raise ValueError(f"unresolved {value}")


def to_px(value: str) -> float:
    m = re.fullmatch(r"([\d.]+)(rem|px)", value)
    if not m:
        raise ValueError(f"not a length: {value}")
    return float(m.group(1)) * (REM if m.group(2) == "rem" else 1)


def to_em(value: str) -> float:
    if value in ("0", "0px", "normal"):
        return 0.0
    m = re.fullmatch(r"(-?[\d.]+)%", value)
    if m:
        return float(m.group(1)) / 100
    m = re.fullmatch(r"(-?[\d.]+)(em|rem|px)", value)
    if m:
        return float(m.group(1)) / (1 if m.group(2) in ("em", "rem") else REM)
    raise ValueError(f"not a letter spacing: {value}")


def parse(css: str, name: str, version: str, scale: float) -> tuple[dict, dict[str, str]]:
    root: dict[str, str] = {}
    dark: dict[str, str] = {}
    for sel, decls in blocks(css):
        names = [s.strip() for s in sel.split(",")]
        if ".dark" in names:
            dark.update(decls)
        elif ":root" in names and ".light" not in names:
            root.update(decls)
    if not dark:
        dark = dict(root)
    scope = {**root, **dark}
    colors: dict[str, str] = {}
    for k, v in dark.items():
        if not k.startswith(("--color-", "--brand-colors-")) or SKIP.search(k):
            continue
        value = resolve(v, scope)
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}|rgba?\(\s*[\d.%\s,/]+\)", value):
            colors[k.removeprefix("--color-").removeprefix("--brand-colors-")] = value.lower()
    RANK = {"l": 2, "m": 1, "s": 0}
    best: dict[tuple[str, str], tuple[int, str]] = {}
    for k, v in scope.items():
        m = TYPE_DECL.fullmatch(k)
        if not m:
            continue
        role, prop = m.group(1), m.group(2)
        pref = re.match(r"--typography-([lms])-", k)
        rank = RANK[pref.group(1)] if pref else 0
        key = (role, prop)
        if key not in best or rank > best[key][0]:
            best[key] = (rank, v)
    per_role: dict[str, dict[str, str]] = {}
    for (role, prop), (_, v) in best.items():
        per_role.setdefault(role, {})[prop] = v
    type_scale: dict[str, dict] = {}
    skipped: dict[str, str] = {}
    for role, props in per_role.items():
        try:
            type_scale[role] = {
                "font-size": to_px(resolve(props["font-size"], scope)) * scale,
                "line-height": to_px(resolve(props["line-height"], scope)) * scale,
                "font-weight": int(resolve(props["font-weight"], scope)),
                "letter-spacing": to_em(resolve(props["letter-spacing"], scope)),
            }
        except KeyError as exc:
            skipped[role] = f"missing {exc.args[0]}"
        except ValueError as exc:
            skipped[role] = str(exc)
    snap = {"name": name, "version": version, "scale": 1, "colors": dict(sorted(colors.items())), "type": type_scale}
    return snap, skipped


def package_field(source: Path, field: str) -> str | None:
    for cand in [source / "package.json", source / "package" / "package.json", source.parent.parent / "package.json"]:
        if cand.exists():
            return json.loads(cand.read_text()).get(field)
    return None


def package_version(source: Path) -> str:
    if source.suffix == ".tgz":
        with tarfile.open(source) as tar:
            return json.load(tar.extractfile("package/package.json"))["version"]
    return package_field(source, "version") or "unknown"


def run_import(source: Path, name: str | None, version: str | None, scale: float, out: Path) -> int:
    css = read_source(source)
    resolved_name = name or package_field(source, "name") or "imported"
    if not re.fullmatch(r"[\w.@-]+", resolved_name):
        raise SystemExit(f"invalid snapshot name {resolved_name!r}: letters, digits, dots, hyphens only")
    snap, skipped = parse(css, resolved_name, version or package_version(source), scale)
    out.write_text(json.dumps(snap, indent=2) + "\n")
    print(f"wrote {out}: {len(snap['colors'])} colours, {len(snap['type'])} type roles (scale x{scale} baked in)")
    for role, why in sorted(skipped.items()):
        print(f"warning: type role '{role}' skipped ({why})", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="generate a theme's tailwind.css from its tokens.json")
    b.add_argument("--theme", default=DEFAULT_THEME)
    b.add_argument("--out", type=Path, default=None)
    b.add_argument("--check", action="store_true")
    i = sub.add_parser("import", help="write a tokens.json snapshot from a design-tokens CSS file")
    i.add_argument("--from", dest="source", type=Path, required=True)
    i.add_argument("--name")
    i.add_argument("--version")
    i.add_argument("--scale", type=float, default=IMPORT_SCALE)
    i.add_argument("--out", type=Path, default=Path("tokens.json"))
    a = ap.parse_args()
    if a.cmd == "build":
        return build(a.theme, a.out, a.check)
    return run_import(a.source, a.name, a.version, a.scale, a.out)


if __name__ == "__main__":
    sys.exit(main())
