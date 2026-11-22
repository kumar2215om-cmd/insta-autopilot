"""Refreshes seo_dates.json after you change a public page: changed pages get today's date, the rest keep theirs.

    python3 tools/seo_dates.py            # today's date
    python3 tools/seo_dates.py 2026-11-22 # a given date
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seo_dates  # noqa: E402

day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
changed = seo_dates.refresh(day)
print(f"{len(changed)} page(s) dated {day}" + ("".join(f"\n  {p}" for p in changed) if changed else ""))
