#!/usr/bin/env python3
"""Warm cache script

Populate the Redis-backed cache (or in-memory fallback) with chapter summaries
and optionally revision answers. This should be run as a background job during
deploy or as a one-off after deploying new content so first-request latency is
eliminated for common queries.

Usage:
  python3 scripts/warm_cache.py --chapters-file data/cleaned_chunks/bio_form1_structured.json
  python3 scripts/warm_cache.py --revision  # also warm revision Q&As

This script intentionally keeps behavior simple and robust: it catches errors
and continues so a failure for one chapter doesn't stop the whole warm-up.
"""

import argparse
import json
import time
import os
from typing import Set

sys_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from src import ai_engine_optimized as optimized


def extract_chapters_from_structured(file_path: str) -> Set[str]:
    with open(file_path, "r", encoding="utf-8") as fh:
        arr = json.load(fh)
    roots = set()
    for item in arr:
        if isinstance(item, dict):
            cr = item.get("chapter_root") or str(item.get("chapter", "")).split(".", 1)[0]
            if cr:
                roots.add(str(cr))
    return roots


def warm(chapters, do_revision: bool = False, delay: float = 1.0):
    print(f"Warming cache for {len(chapters)} chapters (revision={do_revision})")
    def _sort_key(s: str):
        # Return a tuple so numeric chapters sort before non-numeric and all keys
        # are comparable (avoids float vs str TypeError).
        if isinstance(s, str) and s.replace('.', '', 1).isdigit():
            return (0, float(s))
        return (1, s)

    for ch in sorted(chapters, key=_sort_key):
        try:
            print(f"- Summarizing chapter {ch} ...", end=" ")
            res = optimized.summarize_chapter(ch)
            print("done")
        except Exception as e:
            print(f"failed: {e}")

        if do_revision:
            try:
                print(f"  - Warming revision Q&As for {ch} ...", end=" ")
                revs = optimized.answer_revision_questions(ch)
                print(f"done ({len(revs)} items)")
            except Exception as e:
                print(f"failed: {e}")

        time.sleep(delay)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chapters-file", default="data/cleaned_chunks/bio_form1_structured.json")
    p.add_argument("--revision", action="store_true", help="Also warm revision Q&As")
    p.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between chapters")
    args = p.parse_args()

    if not os.path.exists(args.chapters_file):
        print(f"Chapters file not found: {args.chapters_file}")
        return

    chapters = extract_chapters_from_structured(args.chapters_file)
    if not chapters:
        print("No chapters found in structured file.")
        return

    warm(chapters, do_revision=args.revision, delay=args.delay)


if __name__ == "__main__":
    main()
