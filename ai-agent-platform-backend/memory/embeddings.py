"""Embedding generation — abstract interface + offline placeholder.

This step intentionally avoids any external embedding API (OpenAI / local
models). It defines a provider interface so a real backend can be dropped in
later without touching the writer/retriever, plus a deterministic offline
placeholder so the memory engine is fully functional right now.

Public API:

    generate_embedding(text: str) -> list[float]
"""

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List

# Vector size for the placeholder provider. Arbitrary but fixed so every
# vector stored in a collection has a consistent dimension.
EMBEDDING_DIM = 256


class EmbeddingProvider(ABC):
    """Interface every embedding backend must implement."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Return a vector representation of ``text``."""
        raise NotImplementedError


class PlaceholderEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free pseudo-embedding.

    Hashes the input into a fixed-dimension unit vector. Identical text always
    maps to the identical vector, so similarity search behaves sensibly for
    local development and tests. Swap this out for a real provider later.
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        text = text or ""
        seed = text.encode("utf-8")
        vector: List[float] = []
        counter = 0
        while len(vector) < self.dim:
            digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            for byte in digest:
                vector.append((byte / 255.0) * 2.0 - 1.0)  # scale to [-1, 1]
                if len(vector) >= self.dim:
                    break
            counter += 1
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


# Single shared provider instance. A future step can replace this (e.g. read a
# provider name from .env and return an OpenAI-backed implementation).
_provider: EmbeddingProvider = PlaceholderEmbeddingProvider()


def get_embedding_provider() -> EmbeddingProvider:
    """Return the active embedding provider."""
    return _provider


def generate_embedding(text: str) -> List[float]:
    """Generate an embedding vector for ``text`` using the active provider."""
    return get_embedding_provider().embed(text)
