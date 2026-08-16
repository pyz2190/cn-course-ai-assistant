import json
import re
from typing import Any

import httpx2
from pydantic import BaseModel, ConfigDict, Field

from app.domain.rag import (
    GenerationDraft,
    GroundedSentence,
    RetrievedChunk,
)


class _ExternalSentence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class _ExternalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sentences: list[_ExternalSentence] = Field(min_length=1)


class OfflineExtractiveGenerator:
    @property
    def model_id(self) -> str:
        return "offline-extractive-v1"

    def generate(
        self,
        question: str,
        evidence: list[RetrievedChunk],
    ) -> GenerationDraft:
        del question
        if not evidence:
            return GenerationDraft(
                sentences=(
                    GroundedSentence(
                        text="课程资料中没有足够证据回答该问题。",
                        evidence_ids=(),
                    ),
                ),
                resolved_model=self.model_id,
                degraded=True,
            )
        top_chunk = evidence[0].chunk
        sentences = [
            item.strip()
            for item in re.split(r"(?<=[。！？!?])", top_chunk.content)
            if item.strip()
        ]
        selected = sentences[:2] or [top_chunk.content.strip()]
        return GenerationDraft(
            sentences=tuple(
                GroundedSentence(text=sentence, evidence_ids=(top_chunk.chunk_id,))
                for sentence in selected
            ),
            resolved_model=self.model_id,
            degraded=False,
        )


class OpenAICompatibleGenerator:
    """Grounded Chat Completions adapter with strict JSON output validation."""

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str,
        api_key: str | None,
        timeout: httpx2.Timeout,
        max_retries: int,
        client: httpx2.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_id = model_id
        self._api_key = api_key
        self._max_retries = max_retries
        self._client = client or httpx2.Client(timeout=timeout)

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate(
        self,
        question: str,
        evidence: list[RetrievedChunk],
    ) -> GenerationDraft:
        if not evidence:
            return GenerationDraft((), self.model_id, degraded=True)
        payload = {
            "model": self.model_id,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是计算机网络课程助教。只能使用给定证据回答。"
                        "输出 JSON：{\"sentences\":[{\"text\":\"...\","
                        "\"evidence_ids\":[\"chunk id\"]}]}。"
                        "每个事实句必须引用至少一个给定 chunk id；资料不足时直说。"
                    ),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(question, evidence),
                },
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        response: httpx2.Response | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code >= 500 and attempt < self._max_retries:
                    continue
                response.raise_for_status()
                break
            except (httpx2.TimeoutException, httpx2.TransportError):
                if attempt >= self._max_retries:
                    raise
        if response is None:
            raise RuntimeError("external generator produced no response")
        body: dict[str, Any] = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = _ExternalResponse.model_validate(json.loads(content))
        return GenerationDraft(
            sentences=tuple(
                GroundedSentence(
                    text=sentence.text,
                    evidence_ids=tuple(sentence.evidence_ids),
                )
                for sentence in parsed.sentences
            ),
            resolved_model=body.get("model") or self.model_id,
            degraded=False,
        )

    @staticmethod
    def _user_prompt(question: str, evidence: list[RetrievedChunk]) -> str:
        evidence_text = "\n\n".join(
            (
                f"[{item.chunk.chunk_id}]\n"
                f"标题：{item.chunk.title}\n"
                f"章节：{item.chunk.chapter}\n"
                f"内容：{item.chunk.content}"
            )
            for item in evidence
        )
        return f"问题：{question}\n\n证据：\n{evidence_text}"
