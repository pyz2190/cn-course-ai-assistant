# RAG Evaluation Adapter Contract

> Status: Awaiting Member D Confirmation

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

The citation mapping must make it possible to compare returned citations with
an Annotation's `ExpectedCitation`: `resource_id` is required, while
`chunk_id`, chapter, and page fields are compared whenever the expected
citation specifies them. Citation fields not yet confirmed are **待成员 D 确认**;
they must not be fabricated.

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

## Member D Integration Checklist

The following details are **待成员 D 确认**:

- Invocation type: Python function or HTTP API.
- Python module path, callable name, or HTTP endpoint.
- Authentication method and secret injection mechanism.
- Request and response examples.
- Timeout, retry, and retryable-error policy.
- Citation field mapping, including quote, title, chapter, page, and score.
- How resolved model, embedding, reranker, and `top_k` values are obtained.
- How to start the test environment and provide test-only credentials.
- Response schema validation and handling of partial retrieval results.

Until these details are supplied, use `UnconfiguredRagAdapter`, which raises
`NotImplementedError` and produces no fabricated model output.

## Acceptance Criteria

- The adapter receives neither standard answers nor Annotation key points.
- Returned citations can map to `ExpectedCitation` when citation evidence is
  available.
- Requested and adapter-reported runtime parameters are persisted per result.
- Interface failures record errors without fabricating a response.
- Given the same request, runtime parameters, corpus version, and adapter
  configuration, the adapter provides a basically reproducible result.
- Every unresolved field is marked **待成员 D 确认** rather than guessed.
