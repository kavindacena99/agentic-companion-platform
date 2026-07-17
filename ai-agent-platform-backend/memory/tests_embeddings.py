"""Tests for the embedding layer (memory/embeddings.py).

Runs standalone (no Django DB / network needed):

    python -m unittest memory.tests_embeddings

The real-OpenAI semantic-ranking test is skipped unless OPENAI_API_KEY is set.
"""

import math
import os
import unittest

from memory import embeddings
from memory.embeddings import (
    EMBEDDING_DIM,
    OpenAIEmbeddingProvider,
    PlaceholderEmbeddingProvider,
    generate_embedding,
    get_embedding_provider,
    reset_embedding_provider,
)


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class _FakeEmbeddings:
    """Minimal stand-in for client.embeddings with a recorded call."""

    def __init__(self, vector):
        self._vector = vector
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return type("Resp", (), {"data": [type("D", (), {"embedding": self._vector})()]})()


class _FakeClient:
    def __init__(self, vector):
        self.embeddings = _FakeEmbeddings(vector)


class PlaceholderProviderTests(unittest.TestCase):
    def test_dimension_and_unit_norm(self):
        vec = PlaceholderEmbeddingProvider().embed("hello world")
        self.assertEqual(len(vec), EMBEDDING_DIM)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in vec)), 1.0, places=5)

    def test_deterministic(self):
        p = PlaceholderEmbeddingProvider()
        self.assertEqual(p.embed("same text"), p.embed("same text"))
        self.assertNotEqual(p.embed("a"), p.embed("b"))

    def test_empty_text_is_safe(self):
        vec = PlaceholderEmbeddingProvider().embed("")
        self.assertEqual(len(vec), EMBEDDING_DIM)


class OpenAIProviderTests(unittest.TestCase):
    def test_unavailable_without_key_or_client(self):
        self.assertFalse(OpenAIEmbeddingProvider(api_key="").is_available())

    def test_available_with_injected_client(self):
        provider = OpenAIEmbeddingProvider(client=_FakeClient([0.1, 0.2, 0.3]))
        self.assertTrue(provider.is_available())

    def test_embed_calls_api_with_model(self):
        client = _FakeClient([0.1, 0.2, 0.3])
        provider = OpenAIEmbeddingProvider(model="text-embedding-3-small", client=client)
        vec = provider.embed("remember me")
        self.assertEqual(vec, [0.1, 0.2, 0.3])
        self.assertEqual(client.embeddings.last_kwargs["model"], "text-embedding-3-small")
        self.assertEqual(client.embeddings.last_kwargs["input"], "remember me")

    def test_empty_input_is_replaced(self):
        client = _FakeClient([0.0])
        OpenAIEmbeddingProvider(client=client).embed("   ")
        self.assertEqual(client.embeddings.last_kwargs["input"], " ")

    def test_dimensions_passed_when_set(self):
        client = _FakeClient([0.0])
        OpenAIEmbeddingProvider(client=client, dimensions=512).embed("x")
        self.assertEqual(client.embeddings.last_kwargs["dimensions"], 512)


class ProviderSelectionTests(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("EMBEDDING_PROVIDER", "OPENAI_API_KEY")}
        reset_embedding_provider()

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_embedding_provider()

    def test_explicit_placeholder(self):
        os.environ["EMBEDDING_PROVIDER"] = "placeholder"
        reset_embedding_provider()
        self.assertIsInstance(get_embedding_provider(), PlaceholderEmbeddingProvider)

    def test_openai_without_key_falls_back_to_placeholder(self):
        os.environ["EMBEDDING_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = ""
        reset_embedding_provider()
        self.assertIsInstance(get_embedding_provider(), PlaceholderEmbeddingProvider)

    def test_unknown_provider_falls_back(self):
        os.environ["EMBEDDING_PROVIDER"] = "nope"
        reset_embedding_provider()
        self.assertIsInstance(get_embedding_provider(), PlaceholderEmbeddingProvider)

    def test_generate_embedding_uses_active_provider(self):
        os.environ["EMBEDDING_PROVIDER"] = "placeholder"
        reset_embedding_provider()
        self.assertEqual(len(generate_embedding("hi")), EMBEDDING_DIM)


@unittest.skipUnless(os.getenv("OPENAI_API_KEY"), "requires a live OPENAI_API_KEY")
class OpenAISemanticTests(unittest.TestCase):
    """Acceptance: similar sentences rank closer than unrelated ones."""

    def test_semantic_similarity_ordering(self):
        provider = OpenAIEmbeddingProvider()
        base = provider.embed("I am learning artificial intelligence")
        similar = provider.embed("I study AI and machine learning")
        unrelated = provider.embed("The weather in Paris is cold today")
        self.assertGreater(_cosine(base, similar), _cosine(base, unrelated))


if __name__ == "__main__":
    unittest.main()
