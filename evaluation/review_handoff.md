# W1 Review Handoff

> Status: Pending Cross-Review

## Current Dataset

- `question_bank.jsonl`: 12 EvaluationItem records.
- `annotations.jsonl`: 12 EvaluationAnnotation records.
- `evaluation_set.jsonl`: empty; no item is approved.

## Submitted for Cross-Review

All 12 records completed the author self-check and are now `pending_review`:

- `QA-CONCEPT-001`, `QA-CONCEPT-002`
- `QA-PROTOCOL-001`, `QA-PROTOCOL-002`
- `QA-TOOL-001`, `QA-TOOL-002`
- `QA-LAB-001`, `QA-LAB-002`
- `QA-ERROR-001`, `QA-ERROR-002`
- `QA-REVIEW-001`, `QA-REVIEW-002`

There are no remaining `draft` records. Each submitted annotation has
`reviewer: null` and `reviewed_at: null`; this is valid for `pending_review`.

## Evidence and Reviewer Dependencies

- Member B: all 12 items await real source and Chunk locations. Their
  `expected_citations` remain empty until those locations are verifiable.
- Cross-review owner: **待确认**. Do not fill `reviewer` or `reviewed_at` until
  the reviewer is confirmed and has completed the review.
- Member D: if retrieval cannot locate supporting material, investigate the
  retrieval path before any item can be approved.

## TCP Three-Way Handshake Duplicate Check

The six TCP-related records share a knowledge point but have distinct primary
assessment objectives:

- `QA-PROTOCOL-001`: handshake purpose and mechanism.
- `QA-PROTOCOL-002`: SYN, SYN-ACK, ACK order.
- `QA-TOOL-001`: locating and annotating packets in Wireshark.
- `QA-TOOL-002`: deciding completion and checking a submission.
- `QA-LAB-001`: experiment goal, procedure, observation, and judgement.
- `QA-ERROR-002`: correcting an invalid packet-order result from evidence.

Author self-check found no substantive duplicate or answer leakage. The
cross-reviewer must independently confirm that expected answers remain distinct
and request revision if they collapse into the same response.

## Files and Models for Member D

Read the following files together:

- `evaluation/question_bank.jsonl` as `EvaluationItem` records.
- `evaluation/annotations.jsonl` as `EvaluationAnnotation` records.
- `evaluation/evaluation_set.jsonl` as the approved-only target; it must remain
  empty during this review.

Use `EvaluationItem.model_validate(data)` and
`EvaluationAnnotation.model_validate(data)` to parse JSONL records. Match the
two files by `evaluation_id`; do not add source identifiers until they are
verifiable.
