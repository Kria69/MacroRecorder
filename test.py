"""Автоматические проверки проекта.

Запуск вручную:
    python -m unittest -v test_automatic.py

По просьбе заказчика этот файл создан, но пока не запускался.
"""

import gzip
import json
import logging
import tempfile
import unittest
from pathlib import Path

from macro_recorder import profiles


class ProfileValidationTests(unittest.TestCase):
    def test_boolean_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            profiles.validate_events([
                {"time": True, "type": "key_down", "data": {"key": "a"}}
            ])

    def test_events_must_be_sorted(self):
        with self.assertRaises(ValueError):
            profiles.validate_events([
                {"time": 1.0, "type": "key_down", "data": {"key": "a"}},
                {"time": 0.5, "type": "key_up", "data": {"key": "a"}},
            ])

    def test_imported_profile_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps({"name": "Test", "events": []}), encoding="utf-8")
            logger = logging.getLogger("test_profiles")
            name, events = profiles.read_imported_profile(str(path), logger)
            self.assertEqual(name, "Test")
            self.assertEqual(events, [])

    def test_gzip_profile_can_be_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json.gz"
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                json.dump({"name": "Compressed", "events": []}, stream)
            logger = logging.getLogger("test_profiles")
            name, events = profiles.read_imported_profile(str(path), logger)
            self.assertEqual((name, events), ("Compressed", []))


if __name__ == "__main__":
    unittest.main()
