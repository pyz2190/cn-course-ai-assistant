from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.domain.models import ChunkMetadata
from app.domain.rag import RetrievalScope, RetrievedChunk


def create_qdrant_client(
    mode: str,
    *,
    path: Path | None = None,
    url: str | None = None,
    api_key: str | None = None,
) -> QdrantClient:
    if mode == "memory":
        return QdrantClient(location=":memory:")
    if mode == "local":
        if path is None:
            raise ValueError("path is required for local Qdrant")
        path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(path))
    if mode == "remote":
        if not url:
            raise ValueError("url is required for remote Qdrant")
        return QdrantClient(url=url, api_key=api_key)
    raise ValueError(f"unsupported Qdrant mode: {mode}")


class QdrantVectorStore:
    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self._client = client
        self.collection_name = collection_name

    @property
    def store_id(self) -> str:
        return f"qdrant:{self.collection_name}"

    def ensure_index(self, dimension: int) -> None:
        if self._client.collection_exists(self.collection_name):
            collection = self._client.get_collection(self.collection_name)
            vectors = collection.config.params.vectors
            actual_size = vectors.size if isinstance(vectors, models.VectorParams) else None
            if actual_size != dimension:
                raise ValueError(
                    f"collection dimension mismatch: expected {dimension}, got {actual_size}"
                )
            return
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
        )

    def count(self) -> int:
        if not self._client.collection_exists(self.collection_name):
            return 0
        return self._client.count(self.collection_name, exact=True).count

    def upsert(
        self,
        course_id: str,
        chunks: list[ChunkMetadata],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, f"{course_id}:{chunk.chunk_id}")),
                vector=vector,
                payload={
                    "course_id": course_id,
                    "resource_id": chunk.resource_id,
                    "knowledge_point_ids": chunk.knowledge_point_ids,
                    "access_level": chunk.access_level.value,
                    "chunk": chunk.model_dump(mode="json"),
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self._client.upsert(self.collection_name, points=points, wait=True)

    def search(
        self,
        query_vector: list[float],
        scope: RetrievalScope,
        limit: int,
    ) -> list[RetrievedChunk]:
        conditions: list[models.FieldCondition] = [
            models.FieldCondition(
                key="course_id",
                match=models.MatchValue(value=scope.course_id),
            ),
            models.FieldCondition(
                key="access_level",
                match=models.MatchAny(any=[level.value for level in scope.allowed_access_levels]),
            ),
        ]
        if scope.resource_ids:
            conditions.append(
                models.FieldCondition(
                    key="resource_id",
                    match=models.MatchAny(any=list(scope.resource_ids)),
                )
            )
        if scope.knowledge_point_ids:
            conditions.append(
                models.FieldCondition(
                    key="knowledge_point_ids",
                    match=models.MatchAny(any=list(scope.knowledge_point_ids)),
                )
            )
        response = self._client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=models.Filter(must=conditions),
            limit=limit,
            with_payload=True,
        )
        return [self._to_retrieved(point) for point in response.points]

    @staticmethod
    def _to_retrieved(point: Any) -> RetrievedChunk:
        payload = point.payload or {}
        chunk = ChunkMetadata.model_validate(payload["chunk"])
        score = float(point.score)
        return RetrievedChunk(chunk=chunk, retrieval_score=score, final_score=score)
