# Evaluation Module Delivery Checklist

> Status: Phase delivery by Member C; not final acceptance.

## Completed

- 30 EvaluationItem records and their corresponding Annotations are present.
- All six question categories are covered.
- Scoring rules, review workflow, citation handoff, data validation, formal-set
  synchronization, RAG execution framework, human scoring, report generation,
  pipeline entry point, and CI validation are implemented.

## Current Facts

- All 30 Annotations are `pending_review`.
- `approved` count is 0.
- `evaluation_set.jsonl` is empty.
- No real evaluation run result or `baseline.md` exists.
- This module must not be described as finally accepted until citations,
  cross-review, approved data, a real RAG run, and scoring evidence exist.

## Current Blockers

### Member B

- Provide real course resources.
- Provide verified `resource_id` and `chunk_id` pairs.
- Provide inspectable source text, chapters, and page ranges when available.
- Assist the citation review.

### Member D

- Provide a real `RagAdapter`.
- Confirm request, response, and Citation-field mappings.
- Provide model and retrieval runtime parameters.
- Execute the first baseline evaluation with the cross-reviewer.

### Cross-Reviewer

- Review the question, expected answer, `key_points`, and citations.
- Record a real `reviewer` and `reviewed_at` value.
- Mark only passing items as `approved`.

## Required Next Sequence

```text
Member B supplies citations
→ Cross-review approves at least 15 items
→ Synchronize the formal evaluation set
→ Member D integrates the real RAG adapter
→ Run the evaluation
→ Complete human scoring
→ Generate baseline.md
```

## Acceptance Status

File names in this table are relative to `evaluation/` or `scripts/` unless a
different directory is shown. “C” means Member C.

- `bank`: `question_bank.jsonl`; `annotations`: `annotations.jsonl`.
- `scoring`: `scoring_rules.md`; `workflow`: `review_workflow.md`.
- `citation handoff`: `citation_handoff.md`.
- `validator`: `scripts/validate_evaluation_data.py`.
- `sync script`: `scripts/sync_evaluation_set.py`.
- `evaluate script`: `scripts/evaluate.py`.
- `scoring script`: `scripts/score_evaluation_run.py`.
- `report script`: `scripts/generate_evaluation_report.py`.
- `pipeline`: `scripts/run_evaluation_pipeline.py`; `ci.yml`:
  `.github/workflows/ci.yml`.

| Task | Status | Files | Owner | Prerequisite |
| --- | --- | --- | --- | --- |
| Q&A and Annotations | Complete | bank, annotations | C | None |
| Six-category coverage | Complete | question bank | C | None |
| Scoring and review rules | Complete | scoring, workflow | C | None |
| Citation handoff | Complete | citation handoff | C | None |
| Real citations | Blocked | annotations | Member B | resources and Chunks |
| Data validation | Complete | validator | C | dataset files |
| Formal-set sync | Complete | sync script | C | 15 approved items |
| RAG execution framework | Complete | evaluate script | C | D adapter |
| Human scoring | Complete | scoring script | C | real run result |
| Baseline report | Pending | report script | C | scored real run |
| Pipeline and CI | Complete | pipeline, `ci.yml` | C | None |
| Final acceptance | Blocked | `baseline.md` | Team | citation, RAG, scoring |

The framework tasks marked Complete mean that their scripts and documentation
are delivered. They do not mean that the corresponding external evidence or
final baseline has been accepted.
