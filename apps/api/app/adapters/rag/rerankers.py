import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from app.domain.rag import RetrievedChunk


def _terms(text: str) -> set[str]:
    normalized = text.casefold()
    ascii_terms = set(re.findall(r"[a-z0-9][a-z0-9.+/-]*", normalized))
    chinese = re.findall(r"[\u3400-\u9fff]", normalized)
    return ascii_terms | set(chinese) | {
        first + second for first, second in zip(chinese, chinese[1:], strict=False)
    }


class OfflineOverlapReranker:
    @property
    def model_id(self) -> str:
        return "offline-overlap-v1"

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        limit: int,
    ) -> list[RetrievedChunk]:
        query_terms = _terms(question)
        experiment_terms = {"实验", "wireshark", "抓包", "捕获", "nslookup"}
        has_experiment_intent = bool(query_terms & experiment_terms)
        ranked: list[RetrievedChunk] = []
        for item in chunks:
            chunk_terms = _terms(
                " ".join(
                    [
                        item.chunk.title,
                        item.chunk.chapter,
                        item.chunk.content,
                        *item.chunk.knowledge_point_ids,
                    ]
                )
            )
            overlap = len(query_terms & chunk_terms) / max(1, len(query_terms))
            if item.chunk.chapter.startswith("实验") and not has_experiment_intent:
                overlap *= 0.75
            final_score = 0.35 * max(item.retrieval_score, 0) + 0.65 * overlap
            ranked.append(
                replace(item, rerank_score=overlap, final_score=final_score)
            )
        return sorted(
            ranked,
            key=lambda item: (-item.final_score, item.chunk.chunk_id),
        )[:limit]


class BgeReranker:
    def __init__(
        self,
        model_id: str = "BAAI/bge-reranker-v2-m3",
        loader: Callable[..., Any] | None = None,
    ) -> None:
        self._model_id = model_id
        self._loader = loader
        self._model: Any | None = None

    @property
    def model_id(self) -> str:
        return self._model_id

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        limit: int,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []
        pairs = [[question, item.chunk.content] for item in chunks]
        raw_scores = self._load_model().compute_score(pairs, normalize=True)
        scores = [float(raw_scores)] if isinstance(raw_scores, int | float) else raw_scores
        ranked = [
            replace(item, rerank_score=float(score), final_score=float(score))
            for item, score in zip(chunks, scores, strict=True)
        ]
        return sorted(
            ranked,
            key=lambda item: (-item.final_score, item.chunk.chunk_id),
        )[:limit]

    def _load_model(self) -> Any:
        if self._model is None:
            loader = self._loader
            if loader is None:
                try:
                    from FlagEmbedding import FlagReranker
                except ImportError as exc:
                    raise RuntimeError(
                        "BGE reranker requires installation of apps/api[models]"
                    ) from exc
                loader = FlagReranker
            self._model = loader(self.model_id, use_fp16=False)
        return self._model
