"""Tests for the structured canonical-fact store (memory/structured/).

Standalone — each test uses its own temporary SQLite file:

    python -m unittest memory.structured.tests_canonical_store
"""

import os
import shutil
import tempfile
import unittest

from memory.structured.canonical_store import CanonicalFactStore


class CanonicalFactStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="canon_test_")
        self.store = CanonicalFactStore(path=os.path.join(self._tmpdir, "facts.sqlite3"))

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_insert_then_unchanged_then_update(self):
        self.assertEqual(self.store.upsert("u1", "a1", "location", "Colombo"), "inserted")
        self.assertEqual(self.store.upsert("u1", "a1", "location", "Colombo"), "unchanged")
        self.assertEqual(self.store.upsert("u1", "a1", "location", "Kandy"), "updated")

    def test_update_is_in_place_single_row(self):
        self.store.upsert("u1", "a1", "location", "Colombo")
        self.store.upsert("u1", "a1", "location", "Kandy")
        self.assertEqual(self.store.get("u1", "a1", "location"), "Kandy")
        self.assertEqual(self.store.get_all("u1", "a1"), {"location": "Kandy"})  # one row

    def test_case_insensitive_duplicate(self):
        self.store.upsert("u1", "a1", "name", "Kavinda")
        self.assertEqual(self.store.upsert("u1", "a1", "name", "kavinda"), "unchanged")

    def test_get_all_multiple_attributes(self):
        self.store.upsert("u1", "a1", "name", "Sam")
        self.store.upsert("u1", "a1", "location", "Galle")
        self.assertEqual(self.store.get_all("u1", "a1"), {"location": "Galle", "name": "Sam"})

    def test_missing_attribute_returns_none(self):
        self.assertIsNone(self.store.get("u1", "a1", "occupation"))

    def test_delete(self):
        self.store.upsert("u1", "a1", "name", "Sam")
        self.assertEqual(self.store.delete("u1", "a1", "name"), 1)
        self.assertIsNone(self.store.get("u1", "a1", "name"))
        self.assertEqual(self.store.delete("u1", "a1", "name"), 0)  # already gone

    def test_scoping_by_user_and_agent(self):
        self.store.upsert("u1", "a1", "location", "Colombo")
        self.store.upsert("u2", "a1", "location", "Galle")   # different user
        self.store.upsert("u1", "a2", "location", "Kandy")   # different agent
        # Same attribute, three isolated rows — none overwrote another.
        self.assertEqual(self.store.get("u1", "a1", "location"), "Colombo")
        self.assertEqual(self.store.get("u2", "a1", "location"), "Galle")
        self.assertEqual(self.store.get("u1", "a2", "location"), "Kandy")
        self.assertEqual(self.store.get_all("u2", "a1"), {"location": "Galle"})

    def test_persists_across_store_instances(self):
        self.store.upsert("u1", "a1", "name", "Sam")
        reopened = CanonicalFactStore(path=self.store.path)
        self.assertEqual(reopened.get("u1", "a1", "name"), "Sam")


if __name__ == "__main__":
    unittest.main()
