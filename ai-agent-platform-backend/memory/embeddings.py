"""Embedding generation — provider interface + real & offline implementations.

Memory retrieval quality depends entirely on this layer: the writer and the
retriever both call :func:`generate_embedding` and never care which backend is
active. Two providers ship today:

* :class:`OpenAIEmbeddingProvider` — real, semantic embeddings via the OpenAI
  SDK (``text-embedding-3-small`` by default). This is the production default.
* :class:`PlaceholderEmbeddingProvider` — a deterministic, dependency-free
  hash embedding used offline / in tests, and as an automatic fallback when the
  real provider is not configured.

Selection is driven by the environment (see ``get_embedding_provider``), so no
provider is hardcoded and swapping backends never touches the writer/retriever.

Public API::

    generate_embedding(text: str) -> list[float]

.. important::
   A ChromaDB collection fixes its vector dimension on first insert. The
   placeholder (256-dim) and OpenAI (1536-dim by default) vectors are NOT
   compatible. **Changing ``EMBEDDING_PROVIDER`` / ``EMBEDDING_MODEL`` /
   ``EMBEDDING_DIMENSIONS`` requires re-indexing** — delete the persisted store
   at ``CHROMA_DB_PATH`` (or migrate) so collections are rebuilt at the new
   dimension. Mixing dimensions in one collection will raise at query time.
"""

import hashlib
import logging
import math
import os
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger("agent_core")

# Vector size for the placeholder provider. Arbitrary but fixed so every
# placeholder vector stored in a collection has a consistent dimension.
EMBEDDING_DIM = 256

# Default OpenAI embedding model. 1536-dim, cheap, strong for short memories.
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"


class EmbeddingProvider(ABC):
    """Interface every embedding backend must implement."""

    #: Short identifier used in logging / selection (overridden by subclasses).
    name: str = "base"

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Return a vector representation of ``text``."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Whether this provider is configured and usable right now.

        Used by the selector to skip an unconfigured provider without raising.
        Defaults to ``True``; providers that need a key/SDK override this.
        """
        return True


class PlaceholderEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free pseudo-embedding.

    Hashes the input into a fixed-dimension unit vector. Identical text always
    maps to the identical vector, so similarity search is stable for local
    development and tests. It is NOT semantic — unrelated text that happens to
    share tokens will not cluster meaningfully. Use a real provider in prod.
    """

    name = "placeholder"

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


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Real semantic embeddings via the OpenAI SDK.

    The SDK and API key are resolved lazily, so importing this module never
    fails and never makes a network call — ``is_available()`` is safe to probe.
    An explicit ``client`` may be injected (used in tests) to avoid any network
    or key requirement.
    """

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        client=None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("EMBEDDING_MODEL", DEFAULT_OPENAI_MODEL)
        # Optional: OpenAI can return a reduced-dimension vector.
        raw_dims = dimensions if dimensions is not None else os.getenv("EMBEDDING_DIMENSIONS")
        self.dimensions = int(raw_dims) if raw_dims else None
        self._client = client

    def is_available(self) -> bool:
        if self._client is not None:
            return True
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "OpenAIEmbeddingProvider is not configured (missing OPENAI_API_KEY)."
                )
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def embed(self, text: str) -> List[float]:
        client = self._get_client()
        # OpenAI rejects empty input; embed a single space instead.
        payload = text if (text and text.strip()) else " "
        kwargs = {"model": self.model, "input": payload}
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions
        response = client.embeddings.create(**kwargs)
        return list(response.data[0].embedding)


# ----------------------------------------------------------------------
# Provider selection
# ----------------------------------------------------------------------
# Cached active provider. Reset via reset_embedding_provider() (e.g. in tests
# or after changing the environment).
_provider: Optional[EmbeddingProvider] = None


def _build_provider() -> EmbeddingProvider:
    """Construct the provider named by ``EMBEDDING_PROVIDER`` (default openai).

    Falls back to the placeholder — with a warning — when the requested real
    provider is not usable, so local/offline development and tests keep working
    instead of crashing.
    """
    choice = (os.getenv("EMBEDDING_PROVIDER") or "openai").strip().lower()

    if choice == "placeholder":
        logger.info("Embedding provider: placeholder (hash, offline).")
        return PlaceholderEmbeddingProvider()

    if choice == "openai":
        provider = OpenAIEmbeddingProvider()
        if provider.is_available():
            logger.info(
                "Embedding provider: openai (model=%s, dims=%s).",
                provider.model,
                provider.dimensions or "default",
            )
            return provider
        logger.warning(
            "EMBEDDING_PROVIDER=openai but it is not configured "
            "(missing OPENAI_API_KEY or SDK); falling back to placeholder embeddings."
        )
        return PlaceholderEmbeddingProvider()

    logger.warning(
        "Unknown EMBEDDING_PROVIDER=%r; falling back to placeholder embeddings.", choice
    )
    return PlaceholderEmbeddingProvider()


def get_embedding_provider() -> EmbeddingProvider:
    """Return the active embedding provider, building it once on first use."""
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def reset_embedding_provider() -> None:
    """Clear the cached provider so the next call re-reads the environment."""
    global _provider
    _provider = None


def generate_embedding(text: str) -> List[float]:
    """Generate an embedding vector for ``text`` using the active provider."""
    return get_embedding_provider().embed(text)
