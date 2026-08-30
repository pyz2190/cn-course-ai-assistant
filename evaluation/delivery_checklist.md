# Evaluation Module Delivery Checklist

> Status: Phase delivery by Member C; not final acceptance.

## Completed

- 30 EvaluationItem records and their corresponding Annotations are present.
- All six question categories are covered.
- Scoring rules, review workflow, citation handoff, data validation, formal-set
  synchronization, RAG execution framework, human scoring, report generation,
  pipeline entry point, and CI validation are implemented.

## Current Facts

Verified on 2026-08-30 by `python scripts/run_technical_baseline.py`; see
[`reports/technical_baseline.md`](reports/technical_baseline.md).

- All 30 Annotations are `pending_review`.
- `approved` count is 0.
- `evaluation_set.jsonl` is empty.
- No real evaluation run result or `baseline.md` exists.
- All 30 Annotations already carry `expected_citations`, and all 30 resolve to
  Chunks that exist in the corpus. No dangling citation remains.
- The corpus holds 22 Chunks (11 zh + 11 en). They are mock samples, not
  digitised course material, so they still cannot back a formal citation.
- The technical path executes end to end: 30 of 30 questions ran with zero
  errors through `InProcessRagAdapter`.
- 8 of 30 questions return a safe refusal and 16 of 30 hit their expected
  Chunk. This measures corpus coverage, not retrieval quality: the refused
  questions ask about task-engine topics that no Chunk covers.
- This module must not be described as finally accepted until citations,
  cross-review, approved data, a real RAG run, and scoring evidence exist.

## Current Blockers

### Member B

- Provide real course resources. This is now the single largest blocker: the
  corpus covers textbook chapters 2-5 and two labs only, so task-engine
  questions have no material to cite. See
  [`D-003`](../docs/D-003-知识库与问答库建设方案.md) section 7.
- Replace the 22 mock Chunks with digitised course material.
- Provide inspectable source text, chapters, and page ranges when available.
- Assist the citation review.

Resolved since the previous revision: `expected_citations` are populated for
all 30 items and every referenced `chunk_id` resolves.

### Member D

Resolved since the previous revision: `InProcessRagAdapter`
(`apps/api/app/adapters/evaluation.py`) is implemented and wired into
`scripts/evaluate.py --adapter rag`. A technical run over all 30 questions
completes with zero errors, so the adapter is no longer a blocker.

Remaining:

- Execute the first formal baseline evaluation with the cross-reviewer once
  approved items exist.
- Record model and retrieval runtime parameters for that run.

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
- `baseline script`: `scripts/run_technical_baseline.py`; its output:
  `reports/technical_baseline.md` and `reports/technical_baseline.json`.

| Task | Status | Files | Owner | Prerequisite |
| --- | --- | --- | --- | --- |
| Q&A and Annotations | Complete | bank, annotations | C | None |
| Six-category coverage | Complete | question bank | C | None |
| Scoring and review rules | Complete | scoring, workflow | C | None |
| Citation handoff | Complete | citation handoff | C | None |
| Real citations | Partial | annotations | Member B | real course material |
| Technical path verification | Complete | baseline script | C+D | None |
| Data validation | Complete | validator | C | dataset files |
| Formal-set sync | Complete | sync script | C | 15 approved items |
| RAG execution framework | Complete | evaluate script | C | None (adapter delivered) |
| Human scoring | Complete | scoring script | C | real run result |
| Baseline report | Pending | report script | C | scored real run |
| Pipeline and CI | Complete | pipeline, `ci.yml` | C | None |
| Final acceptance | Blocked | `baseline.md` | Team | citation, RAG, scoring |

The framework tasks marked Complete mean that their scripts and documentation
are delivered. They do not mean that the corresponding external evidence or
final baseline has been accepted.
