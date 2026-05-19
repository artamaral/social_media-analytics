import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import extract_returned_ids, find_missing_video_ids


class MissingVideoIdsTest(unittest.TestCase):
    def test_extract_returned_ids_from_youtube_items(self):
        items = [
            {"id": "BH0gnUODKwI", "statistics": {"viewCount": "10"}},
            {"id": "abc123", "statistics": {"viewCount": "20"}},
        ]

        self.assertEqual(
            extract_returned_ids(items),
            ["BH0gnUODKwI", "abc123"],
        )

    def test_missing_ids_include_only_requested_ids_not_returned(self):
        requested_ids = ["BH0gnUODKwI", "lFodaSeTE9A", "abc123"]
        returned_ids = ["abc123"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            ["BH0gnUODKwI", "lFodaSeTE9A"],
        )

    def test_returned_ids_are_never_marked_as_missing(self):
        requested_ids = ["BH0gnUODKwI", "lFodaSeTE9A"]
        returned_ids = ["BH0gnUODKwI", "lFodaSeTE9A"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            [],
        )

    def test_duplicate_requested_ids_are_not_reported_twice(self):
        requested_ids = ["BH0gnUODKwI", "BH0gnUODKwI", "abc123"]
        returned_ids = ["abc123"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            ["BH0gnUODKwI"],
        )

    def test_extra_returned_ids_do_not_create_missing_records(self):
        requested_ids = ["abc123"]
        returned_ids = ["abc123", "extra999"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            [],
        )


if __name__ == "__main__":
    unittest.main()
