#!/usr/bin/env python3
"""
organize.py — Reorganize leurenmoret mirror into a clean assets directory structure.

Before: media/, resources/, theme/  (flat, Sandvox defaults)
After:  assets/images/, assets/css/, assets/js/, assets/theme/

Updates all HTML file references accordingly.
"""

import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Directory mappings: (old_dir, new_dir, extensions)
# ---------------------------------------------------------------------------
MOVES = [
    # media/ -> assets/images/
    (REPO_ROOT / "media",     REPO_ROOT / "assets" / "images",  None),
    # resources/*.css -> assets/css/
    (REPO_ROOT / "resources", REPO_ROOT / "assets" / "css",     {".css"}),
    # resources/*.js  -> assets/js/
    (REPO_ROOT / "resources", REPO_ROOT / "assets" / "js",      {".js"}),
    # theme/main.css, theme/ddsmoothmenu.css -> assets/css/
    (REPO_ROOT / "theme",     REPO_ROOT / "assets" / "css",     {".css"}),
    # theme/nivo-images/ and theme images -> assets/theme/
    (REPO_ROOT / "theme",     REPO_ROOT / "assets" / "theme",   {".jpeg", ".jpg", ".png", ".gif"}),
]

# ---------------------------------------------------------------------------
# Reference replacements in HTML files
# Patterns: path fragments that need rewriting
# ---------------------------------------------------------------------------
REF_REPLACEMENTS = [
    # CSS/JS references from resources/
    (r'href="([^"]*?)resources/([^"]*?\.css)"',   lambda m: f'href="{m.group(1)}assets/css/{m.group(2)}"'),
    (r'src="([^"]*?)resources/([^"]*?\.js)"',     lambda m: f'src="{m.group(1)}assets/js/{m.group(2)}"'),
    # CSS references from theme/
    (r'href="([^"]*?)theme/([^"]*?\.css)"',       lambda m: f'href="{m.group(1)}assets/css/{m.group(2)}"'),
    # Theme images (nivo-images etc.)
    (r'src="([^"]*?)theme/([^"]*?)"',             lambda m: f'src="{m.group(1)}assets/theme/{m.group(2)}"'),
    (r'href="([^"]*?)theme/([^"]*?)"',            lambda m: f'href="{m.group(1)}assets/theme/{m.group(2)}"'),
    # media/ -> assets/images/
    (r'src="([^"]*?)media/([^"]*?)"',             lambda m: f'src="{m.group(1)}assets/images/{m.group(2)}"'),
    (r'href="([^"]*?)media/([^"]*?)"',            lambda m: f'href="{m.group(1)}assets/images/{m.group(2)}"'),
]

COMMENT_HEADER_TEMPLATE = """\
<!--
  Leuren Moret: Global Nuclear Coverup — leurenmoret.info
  Mirror preserved by Kris Yotam | github.com/krisyotam/leurenmoret
  Original site built with Sandvox 2.10.x | Theme: Clockwork Blue
  Content © Leuren Moret & Laurens L. Battis III — all rights reserved
  Archive snapshot: November 2023 | wayback.archive.org/web/*/leurenmoret.info
-->
"""


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def move_files():
    """Move files from old directories to new assets/ structure."""
    print("Moving files to assets/ structure...")
    moved = 0
    for src_dir, dst_dir, exts in MOVES:
        if not src_dir.exists():
            continue
        ensure_dir(dst_dir)
        for src_file in src_dir.rglob("*"):
            if src_file.is_file():
                if exts is not None and src_file.suffix.lower() not in exts:
                    continue
                # Preserve subdirectory structure relative to src_dir
                rel = src_file.relative_to(src_dir)
                dst_file = dst_dir / rel
                ensure_dir(dst_file.parent)
                if not dst_file.exists():
                    shutil.copy2(src_file, dst_file)
                    moved += 1
    print(f"  Copied {moved} files into assets/")


def update_html_refs():
    """Update all HTML files to use new assets/ paths."""
    print("Updating HTML references...")
    html_files = list(REPO_ROOT.rglob("*.html"))
    # Exclude assets/ dir if it already has HTML (unlikely)
    html_files = [f for f in html_files if "assets" not in f.parts]
    updated = 0
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="replace")
        original = content
        for pattern, replacement in REF_REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        if content != original:
            html_file.write_text(content, encoding="utf-8")
            updated += 1
    print(f"  Updated {updated} HTML files")


def add_comment_headers():
    """Insert a preservation comment header after <!DOCTYPE html> in each HTML file."""
    print("Adding comment headers...")
    html_files = list(REPO_ROOT.rglob("*.html"))
    html_files = [f for f in html_files if "assets" not in f.parts]
    added = 0
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="replace")
        # Skip if already has our header
        if "Mirror preserved by Kris Yotam" in content:
            continue
        # Insert after <!DOCTYPE html> line
        if "<!DOCTYPE html>" in content:
            content = content.replace(
                "<!DOCTYPE html>",
                f"<!DOCTYPE html>\n{COMMENT_HEADER_TEMPLATE}",
                1,
            )
            html_file.write_text(content, encoding="utf-8")
            added += 1
        elif content.strip().startswith("<html"):
            content = f"{COMMENT_HEADER_TEMPLATE}{content}"
            html_file.write_text(content, encoding="utf-8")
            added += 1
    print(f"  Added headers to {added} HTML files")


def remove_old_dirs():
    """Remove original media/, resources/, theme/ directories after successful migration."""
    old_dirs = [
        REPO_ROOT / "media",
        REPO_ROOT / "resources",
        REPO_ROOT / "theme",
    ]
    for d in old_dirs:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d.name}/")


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be changed")
        print(f"Repo root: {REPO_ROOT}")
        print(f"HTML files: {len(list(REPO_ROOT.rglob('*.html')))}")
        for src_dir, dst_dir, exts in MOVES:
            if src_dir.exists():
                count = sum(1 for f in src_dir.rglob("*") if f.is_file() and (exts is None or f.suffix.lower() in exts))
                print(f"  {src_dir.name}/ -> {dst_dir.relative_to(REPO_ROOT)}/ ({count} files)")
        return

    print(f"Organizing {REPO_ROOT}")
    move_files()
    update_html_refs()
    add_comment_headers()
    print("\nDone. Old directories still in place — review before removing.")
    print("To remove originals, re-run with --remove-old")

    if "--remove-old" in sys.argv:
        remove_old_dirs()


if __name__ == "__main__":
    main()
