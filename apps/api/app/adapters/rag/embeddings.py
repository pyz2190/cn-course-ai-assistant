import hashlib
import math
import re
from collections.abc import Callable
from typing import Any


def _fragments(text: str) -> list[str]:
    normalized = text.casefold().strip()
    fragments = re.findall(r"[a-z0-9][a-z0-9.+/-]*|[\u3400-\u9fff]", normalized)
    chinese = [item for item in fragments if len(item) == 1 and "\u3400" <= item <= "\u9fff"]
    fragments.extend(a + b for a, b in zip(chinese, chinese[1:], strict=False))
    return fragments


class OfflineHashEmbedding:
    """Small deterministic feature-hashing embedding for offline development."""

    def __init__(self, dimension: int = 384) -> None:
        if dimension < 32:
            raise ValueError("dimension must be at least 32")
        self._dimension = dimension

    @property
    def model_id(self) -> str:
        return f"offline-hash-v1-{self.dimension}d"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for fragment in _fragments(text):
            digest = hashlib.blake2b(fragment.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            return [value / norm for value in vector]
        return vector


class BgeM3Embedding:
    """Lazy FlagEmbedding adapter; model weights are never loaded by default."""

    def __init__(
        self,
        model_id: str = "BAAI/bge-m3",
        dimension: int = 1024,
        loader: Callable[..., Any] | None = None,
    ) -> None:
        self._model_id = model_id
        self._dimension = dimension
        self._loader = loader
        self._model: Any | None = None

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        output = self._load_model().encode(texts, batch_size=8, normalize_embeddings=True)
        dense = output["dense_vecs"] if isinstance(output, dict) else output
        return [list(map(float, vector)) for vector in dense]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _load_model(self) -> Any:
        if self._model is None:
            loader = self._loader
            if loader is None:
                try:
                    from FlagEmbedding import BGEM3FlagModel
                except ImportError as exc:
                    raise RuntimeError(
                        "BGE embedding requires installation of apps/api[models]"
                    ) from exc
                loader = BGEM3FlagModel
            self._model = loader(self.model_id, use_fp16=False)
        return self._model
