# RAG Evaluation Adapter Contract

> Status: Confirmed by Member D on 2026-08-16

## Boundary

`scripts/evaluate.py` owns evaluation-set validation, run IDs, per-item result
records, requested runtime parameters, and report writing. Member D supplies a
`RagAdapter` implementation. The adapter must answer a sanitized evaluation
request and must not decide approval, scores, or evaluation-set membership.

## Input

The adapter entry point is:

```python
RagAdapter.answer(item: RagRequest, runtime: RuntimeParameters) -> AdapterResponse
```

`RagRequest` contains only:

- `evaluation_id`
- `question`
- `knowledge_point_ids`

`RuntimeParameters` contains the requested `model`, `embedding`, `reranker`,
`top_k`, and the repository `git_commit`. Member D may add reported runtime
metadata through `AdapterResponse.runtime`, but must not alter the requested
parameters.

Do not pass `expected_answer` to the RAG adapter. Do not pass Annotation
`key_points` either. Both are evaluation references and would leak the expected
answer into generation. `knowledge_point_ids` are allowed because they scope
retrieval without exposing the target answer.

## Output

Return one response per request:

```python
AdapterResponse(
    generated_answer="...",
    citations=[...],
    runtime={...},
)
```

`generated_answer` is the model output without post-hoc answer substitution.
`citations` is a list of source records. `runtime` is optional adapter-reported
metadata, such as the resolved model version or retrieval latency. The runner
records requested parameters, Git commit, and this adapter metadata in the run
report.

Each citation must provide:

- `resource_id`
- `chunk_id`
- Citation title
- Original quote or a verifiable summary
- Chapter and page range when present in the source
- Retrieval score when available

The citation mapping makes it possible to compare returned citations with an
Annotation's `ExpectedCitation`: `resource_id` and `chunk_id` are returned;
`title`, `quote`, `chapter`, `page_start`, `page_end`, `source_url`,
`retrieval_score`, and `rerank_score` are returned when available. All source
fields are filled by `CitationAssembler` from a Chunk in the current retrieval
result. A generator cannot create these fields.

## Error Handling

Record the following errors in the affected item's report result, with an empty
`generated_answer` and an empty `citations` list. Continue with later items.

| Error | Per-item handling |
| --- | --- |
| Interface unavailable | Record the adapter exception. |
| Request timeout | Record timeout type and configured timeout. |
| Response format invalid | Record validation or mapping failure. |
| Empty answer | Record that no answer was returned. |
| Missing citations | Record that the response has no citations. |
| Citation cannot be traced | Record the unresolvable citation fields. |

Terminate the whole run before any adapter call only for invalid evaluation-set
data, unreadable input files, or an invalid run configuration that prevents a
consistent execution plan. A process-wide interface outage may be represented
as per-item failures so the report remains complete; the final exit code must
indicate execution failure. No error path may invent an answer or citation.

## Member D Integration

- Invocation: in-process Python function.
- Adapter: `app.adapters.evaluation.InProcessRagAdapter`.
- Service: the same cached `app.core.dependencies.get_rag_service()` used by
  the API.
- CLI selection: `python scripts/evaluate.py --adapter rag`.
- Authentication: none for the in-process adapter. Optional external model and
  remote Qdrant secrets use `CN_AI_MODEL_API_KEY` and
  `CN_AI_QDRANT_API_KEY`; no secret is accepted in an evaluation item.
- Default test environment: offline embedding, in-memory Qdrant, offline
  reranker and extractive generator; no credentials, network, paid call, or
  model download.
- External HTTP policy: connect/read/write/pool timeouts default to
  3/30/10/3 seconds, with one retry. A final failure falls back to offline
  extraction when degradation is enabled.
- Runtime resolution: `RagRuntime` reports the actual model, embedding,
  reranker, vector store, `top_k`, `fetch_k`, stage timings, and corpus
  version. The runner separately preserves the requested values and Git
  commit.
- Partial retrieval: no result or low relevance returns a grounded refusal
  with no citations; an unavailable reranker may return initial retrieval
  results with a degraded marker.
- Response validation: external generation must return strict JSON sentences
  and evidence IDs. Unknown evidence IDs are discarded and cannot create a
  Citation.

`UnconfiguredRagAdapter` remains available only when the CLI explicitly uses
`--adapter unconfigured` (the compatibility default).

## Acceptance Criteria

- The adapter receives neither standard answers nor Annotation key points.
- Returned citations can map to `ExpectedCitation` when citation evidence is
  available.
- Requested and adapter-reported runtime parameters are persisted per result.
- Interface failures record errors without fabricating a response.
- Given the same request, runtime parameters, corpus version, and adapter
  configuration, the adapter provides a basically reproducible result.
- No unresolved citation or invocation field is guessed.
