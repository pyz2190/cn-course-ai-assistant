# W2 Review Handoff

> Status: Pending Cross-Review

## Current Dataset

- `question_bank.jsonl`: 30 EvaluationItem records.
- `annotations.jsonl`: 30 EvaluationAnnotation records.
- Review status: 30 `pending_review`; no `draft`, `approved`, or `rejected`
  records.
- `evaluation_set.jsonl`: empty; no item is approved.

## Submitted for Cross-Review

Every record has completed the author self-check. Each submitted annotation has
`reviewer: null`, `reviewed_at: null`, and no formal citation yet; these values
are valid for `pending_review`.

- Concept: `QA-CONCEPT-001` through `QA-CONCEPT-005`.
- Protocol detail: `QA-PROTOCOL-001` through `QA-PROTOCOL-005`.
- Tool tutorial: `QA-TOOL-001` through `QA-TOOL-005`.
- Lab: `QA-LAB-001` through `QA-LAB-005`.
- Common error: `QA-ERROR-001` through `QA-ERROR-005`.
- Review: `QA-REVIEW-001` through `QA-REVIEW-005`.

## Evidence and Reviewer Dependencies

- Member B: all 30 items await real course-resource and Chunk locations.
  `expected_citations` remains empty until those locations and their content
  are independently verifiable.
- Cross-review owner: **待确认**. Do not fill `reviewer` or `reviewed_at`
  until the reviewer is confirmed and has completed the review.
- Member D: if retrieval cannot locate material that supports an answer and
  its `key_points`, investigate the retrieval path before approval.

## Topic-Duplication Check

The TCP/Wireshark items intentionally share one knowledge point but have
different assessment targets:

- `QA-PROTOCOL-001`: handshake purpose and bidirectional capability.
- `QA-PROTOCOL-002`: packet order.
- `QA-PROTOCOL-003`: the confirmation role of each packet type.
- `QA-PROTOCOL-004`: bidirectional initial-sequence-number synchronization.
- `QA-CONCEPT-004`: why packet class and sequence-number observations are both
  needed.
- `QA-TOOL-001`: locating and annotating the packets.
- `QA-TOOL-002`: completion and pre-submission checks.
- `QA-TOOL-003`: producing a reviewable packet-number and sequence-number
  record.
- `QA-LAB-001`: experiment design and completion judgement.
- `QA-ERROR-002`: correcting an invalid packet-order result from evidence.

DNS items distinguish protocol evidence correlation (`QA-PROTOCOL-005`),
evidence recording (`QA-TOOL-004`), lab procedure (`QA-LAB-002`), insufficient
evidence handling (`QA-ERROR-003`), and report review (`QA-REVIEW-003`).
Network-design items distinguish address conflict, topology deliverables,
single-point-of-failure correction, and integrated design review. The author
self-check found no answer leakage or substantive duplicate; the cross-reviewer
must independently confirm this conclusion.

## Files and Models for Member D

Read these files together:

- `evaluation/question_bank.jsonl` as `EvaluationItem` records.
- `evaluation/annotations.jsonl` as `EvaluationAnnotation` records.
- `evaluation/evaluation_set.jsonl` as the approved-only target; it must remain
  empty during this review.

Use `EvaluationItem.model_validate(data)` and
`EvaluationAnnotation.model_validate(data)` to parse JSONL records. Match the
two files by `evaluation_id`; do not add source identifiers until they are
verifiable.
