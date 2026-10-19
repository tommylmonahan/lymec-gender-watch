import json
import unittest

import server


class JsonStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        server.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.original_records_file = server.RECORDS_FILE
        self.original_archive_directory = server.ARCHIVE_DIR
        self.test_records_file = server.DATA_DIR / ".test-records.json"
        self.created_archive_file = None
        server.RECORDS_FILE = self.test_records_file
        server.ARCHIVE_DIR = server.DATA_DIR

    def tearDown(self) -> None:
        server.RECORDS_FILE = self.original_records_file
        server.ARCHIVE_DIR = self.original_archive_directory
        self.test_records_file.unlink(missing_ok=True)
        if self.created_archive_file is not None:
            self.created_archive_file.unlink(missing_ok=True)

    def test_write_load_and_archive_use_json_only(self) -> None:
        entries = [
            {
                "id": "record-1",
                "gender": "Other",
                "firstTime": True,
                "comment": "Opening intervention",
                "timestamp": "2026-10-19T10:00:00Z",
            }
        ]

        server.write_records(entries)
        self.assertEqual(server.load_records(), entries)

        self.created_archive_file = server.ROOT / server.archive_records(entries)
        self.assertEqual(self.created_archive_file.suffix, ".json")
        self.assertEqual(
            json.loads(self.created_archive_file.read_text(encoding="utf-8")),
            entries,
        )
        self.assertEqual(list(server.DATA_DIR.rglob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
