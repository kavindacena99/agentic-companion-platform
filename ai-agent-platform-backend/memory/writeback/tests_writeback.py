"""Tests for agentic memory writeback (decide / dedup / update).

Runs standalone against an in-memory ChromaDB with placeholder embeddings:

    python -m unittest memory.writeback.tests_writeback

Acceptance covered: repeating a known fact does not duplicate it; a changed
canonical fact updates in place; every write stays scoped to user + agent.
"""

import os
import shutil
import tempfile
import unittest

from memory import chroma_client
from memory.collections import USER_MEMORY
from memory.embeddings import reset_embedding_provider
from memory.memory_retriever import search_memory
from memory.memory_service import get_canonical_facts
from memory.memory_writer import get_memory, store_memory, update_memory
from memory.structured.canonical_store import reset_canonical_store
from memory.writeback.fact_extractor import extract_facts
from memory.writeback.memory_updater import decide_write, should_store
from memory.writeback.writeback_engine import process_writeback


# ---------------------------------------------------------------------------
# Pure helpers (no DB)
# ---------------------------------------------------------------------------
class ShouldStoreTests(unittest.TestCase):
    def test_floor_keeps_medium_and_high(self):
        self.assertTrue(should_store({"content": "x", "importance": "high"}))
        self.assertTrue(should_store({"content": "x", "importance": "medium"}))

    def test_floor_skips_low(self):
        self.assertFalse(should_store({"content": "x", "importance": "low"}))

    def test_empty_content_skipped(self):
        self.assertFalse(should_store({"content": "  ", "importance": "high"}))


class ExtractFactsTaggingTests(unittest.TestCase):
    def test_location_is_canonical(self):
        facts = extract_facts("i live in Colombo", "")
        location = [f for f in facts if f.get("attribute") == "location"]
        self.assertEqual(len(location), 1)
        self.assertTrue(location[0]["canonical"])
        self.assertEqual(location[0]["content"], "User lives in Colombo")

    def test_moved_to_maps_to_location_attribute(self):
        facts = extract_facts("i moved to Kandy", "")
        location = [f for f in facts if f.get("attribute") == "location"]
        self.assertEqual(location[0]["content"], "User lives in Kandy")

    def test_name_is_canonical(self):
        facts = extract_facts("my name is Sam", "")
        name = [f for f in facts if f.get("attribute") == "name"]
        self.assertTrue(name and name[0]["canonical"])

    def test_likes_is_not_canonical(self):
        facts = extract_facts("i love hiking", "")
        likes = [f for f in facts if "likes" in f["content"]]
        self.assertTrue(likes and not likes[0]["canonical"])


# ---------------------------------------------------------------------------
# DB-backed tests
# ---------------------------------------------------------------------------
class _MemoryDBTest(unittest.TestCase):
    def setUp(self):
        # Unique on-disk store per test → real isolation (chromadb caches
        # clients by path, so distinct paths never share state) and placeholder
        # embeddings so no network / API key is needed.
        self._saved_provider = os.environ.get("EMBEDDING_PROVIDER")
        self._saved_path = os.environ.get("CHROMA_DB_PATH")
        self._saved_canon = os.environ.get("CANONICAL_DB_PATH")
        os.environ["EMBEDDING_PROVIDER"] = "placeholder"
        reset_embedding_provider()
        self._tmpdir = tempfile.mkdtemp(prefix="wb_test_")
        os.environ["CHROMA_DB_PATH"] = self._tmpdir
        # Isolate the structured store too, so canonical facts don't leak.
        os.environ["CANONICAL_DB_PATH"] = os.path.join(self._tmpdir, "canon.sqlite3")
        reset_canonical_store()
        self._saved_client = chroma_client._client
        chroma_client._client = None

    def tearDown(self):
        chroma_client._client = self._saved_client
        for key, value in (
            ("EMBEDDING_PROVIDER", self._saved_provider),
            ("CHROMA_DB_PATH", self._saved_path),
            ("CANONICAL_DB_PATH", self._saved_canon),
        ):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_embedding_provider()
        reset_canonical_store()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _location_records(self, user="u1", agent="a1"):
        hits = search_memory(USER_MEMORY, "User lives in", user, agent, top_k=20)
        return [h["content"] for h in hits if h["content"] and "lives in" in h["content"]]


class WriterPrimitiveTests(_MemoryDBTest):
    def test_update_replaces_content_and_preserves_scope(self):
        rid = store_memory(USER_MEMORY, "u1", "a1", "User lives in Colombo", {"attribute": "location"})
        update_memory(USER_MEMORY, rid, "User lives in Kandy", {"attribute": "location"})
        record = get_memory(USER_MEMORY, rid)
        self.assertEqual(record["content"], "User lives in Kandy")
        self.assertEqual(record["metadata"]["user_id"], "u1")
        self.assertEqual(record["metadata"]["agent_id"], "a1")
        self.assertIn("updated_at", record["metadata"])


class DecideWriteTests(_MemoryDBTest):
    def _fact(self, content, attribute=None, canonical=False, importance="high", type_="user_fact"):
        return {"content": content, "attribute": attribute, "canonical": canonical,
                "importance": importance, "type": type_}

    def test_new_fact_inserts(self):
        result = decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        self.assertEqual(result["action"], "insert")

    def test_repeated_canonical_fact_is_skipped(self):
        fact = self._fact("User lives in Colombo", "location", True)
        decide_write(USER_MEMORY, "u1", "a1", fact)
        result = decide_write(USER_MEMORY, "u1", "a1", fact)
        self.assertEqual(result["action"], "skip")
        self.assertEqual(result["reason"], "duplicate")
        self.assertEqual(self._location_records(), ["User lives in Colombo"])

    def test_changed_canonical_fact_updates_in_place(self):
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        result = decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Kandy", "location", True))
        self.assertEqual(result["action"], "update")
        # Exactly one location memory remains, with the new value.
        self.assertEqual(self._location_records(), ["User lives in Kandy"])

    def test_near_duplicate_noncanonical_is_skipped(self):
        fact = self._fact("User likes hiking", None, False, "medium")
        self.assertEqual(decide_write(USER_MEMORY, "u1", "a1", fact)["action"], "insert")
        self.assertEqual(decide_write(USER_MEMORY, "u1", "a1", fact)["action"], "skip")

    def test_scoping_is_per_user_and_agent(self):
        # Same attribute, different user → must NOT update the other user's fact.
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        result = decide_write(USER_MEMORY, "u2", "a1", self._fact("User lives in Galle", "location", True))
        self.assertEqual(result["action"], "insert")  # new user → fresh insert, not update
        self.assertEqual(self._location_records("u1", "a1"), ["User lives in Colombo"])
        self.assertEqual(self._location_records("u2", "a1"), ["User lives in Galle"])

    def test_different_agent_does_not_collide(self):
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        result = decide_write(USER_MEMORY, "u1", "a2", self._fact("User lives in Kandy", "location", True))
        self.assertEqual(result["action"], "insert")

    def test_canonical_fact_lands_in_structured_store(self):
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User's name is Sam", "name", True))
        self.assertEqual(
            get_canonical_facts("u1", "a1"),
            {"location": "User lives in Colombo", "name": "User's name is Sam"},
        )

    def test_structured_store_updates_on_contradiction(self):
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Colombo", "location", True))
        decide_write(USER_MEMORY, "u1", "a1", self._fact("User lives in Kandy", "location", True))
        # SQL holds exactly one, current value — vectors stayed in sync too.
        self.assertEqual(get_canonical_facts("u1", "a1"), {"location": "User lives in Kandy"})
        self.assertEqual(self._location_records(), ["User lives in Kandy"])


class ProcessWritebackTests(_MemoryDBTest):
    def _turn(self, message, user="u1", agent="a1"):
        return process_writeback(user, agent, [{"role": "user", "content": message}], "ok")

    def test_repeat_does_not_duplicate_and_change_updates(self):
        self._turn("my name is Kavinda and i live in Colombo")
        # Repeat the same location → no duplicate.
        again = self._turn("i live in Colombo")
        self.assertTrue(any(u.get("action") == "skip" and u.get("content") == "User lives in Colombo" for u in again))
        # Change it → update in place.
        moved = self._turn("i moved to Kandy")
        self.assertTrue(any(u.get("action") == "update" and u.get("content") == "User lives in Kandy" for u in moved))
        self.assertEqual(self._location_records(), ["User lives in Kandy"])

    def test_low_importance_fact_is_skipped(self):
        updates = self._turn("i have a red bicycle")
        skipped = [u for u in updates if u.get("content", "").startswith("User has")]
        self.assertTrue(skipped and skipped[0]["action"] == "skip")


if __name__ == "__main__":
    unittest.main()
