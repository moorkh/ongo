#!/usr/bin/env python3
"""Unit tests for ongo-site's date-time sort ordering.

Verifies:
  * Same-date publications are ordered by time-of-day (newest first).
  * Same-second publications fall back to title (A->Z) as a stable tiebreaker.
  * Items whose date is derived from the note's *key/title* (not created_at)
    pad to ``00:00:00`` and so always sort AFTER same-date ongo-published
    items on the same date.
  * `_invert_date` is monotone-descending across full timestamps.

The ongo-site script has no `.py` extension, so we load it as a module via
``importlib.util``.
"""

import importlib.util
import importlib.machinery
import os
import sys
import unittest


_HERE = os.path.dirname(os.path.abspath(__file__))
_SITE_SCRIPT = os.path.normpath(os.path.join(_HERE, "..", "bin", "ongo-site"))


def _load():
    # ongo-site has no .py extension, so we need an explicit SourceFileLoader.
    loader = importlib.machinery.SourceFileLoader("ongo_site", _SITE_SCRIPT)
    spec = importlib.util.spec_from_loader("ongo_site", loader)
    mod = importlib.util.module_from_spec(spec)
    # The script's top level is import-safe (all execution is guarded by
    # ``if __name__ == "__main__":``).
    loader.exec_module(mod)
    return mod


class SortByDateTimeTests(unittest.TestCase):
    def setUp(self):
        self.os = _load()

    def test_invert_date_descending_on_full_timestamp(self):
        inv = self.os._invert_date
        # Later timestamp -> smaller inverted key (so ascending sort = newest first).
        self.assertLess(
            inv("2026-05-30 14:30:00"),
            inv("2026-05-30 09:15:00"),
        )
        self.assertLess(
            inv("2026-05-30 00:00:00"),
            inv("2026-05-29 23:59:59"),
        )

    def test_derive_sort_ts_uses_time_when_dates_match(self):
        # date_key derived from created_at -> time-of-day applies.
        self.assertEqual(
            self.os.derive_sort_ts("2026-05-30", "2026-05-30 14:30:00"),
            "2026-05-30 14:30:00",
        )

    def test_derive_sort_ts_pads_when_dates_disagree(self):
        # date_key from note key (e.g. paper from 2020) — created_at time is
        # NOT a meaningful time-of-day for that historical date.
        self.assertEqual(
            self.os.derive_sort_ts("2020-05-15", "2026-05-30 14:30:00"),
            "2020-05-15 00:00:00",
        )

    def test_derive_sort_ts_no_created_at(self):
        self.assertEqual(
            self.os.derive_sort_ts("2026-05-30", None),
            "2026-05-30 00:00:00",
        )

    def test_same_day_items_sort_by_time(self):
        # Three items on the same day, very different times.
        items = [
            {"display": "alpha", "sort_ts": "2026-05-30 09:00:00"},
            {"display": "beta",  "sort_ts": "2026-05-30 14:30:00"},
            {"display": "gamma", "sort_ts": "2026-05-30 02:15:00"},
        ]
        ordered = sorted(
            items,
            key=lambda x: (
                self.os._invert_date(x["sort_ts"]),
                x["display"].lower(),
            ),
        )
        # Newest time first.
        self.assertEqual(
            [i["display"] for i in ordered],
            ["beta", "alpha", "gamma"],
        )

    def test_same_second_falls_back_to_title(self):
        items = [
            {"display": "Charlie", "sort_ts": "2026-05-30 10:00:00"},
            {"display": "alpha",   "sort_ts": "2026-05-30 10:00:00"},
            {"display": "Bravo",   "sort_ts": "2026-05-30 10:00:00"},
        ]
        ordered = sorted(
            items,
            key=lambda x: (
                self.os._invert_date(x["sort_ts"]),
                x["display"].lower(),
            ),
        )
        self.assertEqual(
            [i["display"] for i in ordered],
            ["alpha", "Bravo", "Charlie"],
        )

    def test_cross_day_ordering(self):
        items = [
            {"display": "yesterday-late",
             "sort_ts": "2026-05-29 23:59:59"},
            {"display": "today-early",
             "sort_ts": "2026-05-30 00:00:01"},
            {"display": "today-late",
             "sort_ts": "2026-05-30 14:30:00"},
        ]
        ordered = sorted(
            items,
            key=lambda x: (
                self.os._invert_date(x["sort_ts"]),
                x["display"].lower(),
            ),
        )
        self.assertEqual(
            [i["display"] for i in ordered],
            ["today-late", "today-early", "yesterday-late"],
        )

    def test_date_only_items_sort_after_timestamped_same_date(self):
        # Item whose date came from key/title (padded 00:00:00) should sort
        # AFTER same-date ongo-published items that have a real time-of-day.
        items = [
            {"display": "ongo-published-mid",
             "sort_ts": "2026-05-30 12:00:00"},
            {"display": "ongo-published-early",
             "sort_ts": "2026-05-30 06:00:00"},
            {"display": "historical-paper",
             "sort_ts": "2026-05-30 00:00:00"},
        ]
        ordered = sorted(
            items,
            key=lambda x: (
                self.os._invert_date(x["sort_ts"]),
                x["display"].lower(),
            ),
        )
        self.assertEqual(
            [i["display"] for i in ordered],
            ["ongo-published-mid",
             "ongo-published-early",
             "historical-paper"],
        )


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
