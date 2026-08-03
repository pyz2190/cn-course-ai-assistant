# Evaluation Review Workflow

> Status: Draft

## Status Model

The workflow uses the values in `EvaluationReviewStatus` exactly:

```text
draft
→ pending_review
→ approved

pending_review
→ rejected
→ revised
→ pending_review
→ approved
```

- `draft`: The author is performing a self-check. Complete the item,
  annotation, and self-check before submitting it.
- `pending_review`: The item is waiting for cross-review. A reviewer records a
  review decision and evidence.
- `approved`: The item may enter the formal evaluation set. Keep reviewer and
  review time in the annotation.
- `rejected`: The review did not pass. Record actionable review notes before
  returning the item for revision.
- `revised`: The author has updated the item in response to review notes.
  Resubmit for cross-review; it cannot be approved directly.

Only `approved` items may be written to `evaluation/evaluation_set.jsonl`.
Items in every other status, including `draft`, remain outside the formal
evaluation set. The current W1 items are all `draft`; none may be changed to
`approved` without cross-review.

## Review Procedure

1. The author completes the question, expected answer, and matching
   annotation, then performs the `draft` self-check.
2. The author changes the item to `pending_review` and supplies the material
   needed for a reviewer to verify it.
3. A cross-reviewer checks the item against the checklist below. A passing item
   becomes `approved`; a failing item becomes `rejected` with actionable
   `review_notes`.
4. The author or responsible role addresses the notes and marks the work
   `revised`.
5. The revised item returns to `pending_review` for another cross-review. It
   may move to `approved` only after that review.

For both `approved` and `rejected`, the annotation must contain a non-empty
`reviewer` and `reviewed_at`, as required by the model. Approval must not be
used as a shortcut for unresolved evidence or review work.

## Review Checklist

Review every question-answer pair and its annotation for all of the following:

1. The question is clear, bounded, and does not disclose its answer.
2. The expected answer is correct for the supported course scope.
3. `key_points` are complete, non-duplicated, and independently judgeable.
4. The category and difficulty match the primary assessment objective.
5. Every knowledge point ID exists in the project’s supported data.
6. Every citation is real and supports the stated conclusion. If real citation
   locations are not yet available, keep `expected_citations` empty and do not
   approve the item on the assumption that a citation will be added later.
7. The item does not duplicate another question, duplicate another expected
   answer, or leak its conclusion in the question text.

### TCP Three-Way Handshake Duplicate Review

The W1 bank contains several TCP three-way-handshake items. Cross-review must
compare their assessment objectives, not only their IDs or categories:

- `QA-PROTOCOL-001` assesses the purpose of the handshake.
- `QA-PROTOCOL-002` assesses the SYN, SYN-ACK, ACK sequence.
- `QA-TOOL-001` and `QA-TOOL-002` assess capture-analysis operation and
  submission verification.
- `QA-LAB-001` assesses experimental design and result judgement.
- `QA-ERROR-002` assesses correction after an invalid packet-order result.

If the expected answers substantially collapse to the same response, the
reviewer must reject the redundant item or request a revision; different
category labels alone do not make the items distinct.

## Issue Routing

The following role routing applies. Individual names and final ownership are
**待确认**; do not assign a specific person in annotations until the team
confirms it.

- Incorrect question or expected answer: Member C (specific owner: **待确认**)
  revises the content, then moves it to `revised`.
- Missing material or citation: Member B (specific owner: **待确认**) supplies
  verifiable source information.
- Incorrect Chunk splitting or location: Member B (specific owner:
  **待确认**) corrects the Chunk or location evidence.
- Correct material cannot be retrieved: Member D (specific owner:
  **待确认**) investigates retrieval and provides findings.
- Citation display or traceability error: Member D (specific owner:
  **待确认**) corrects the retrieval or display trace.
- Demo presentation issue: Member E (specific owner: **待确认**) corrects the
  demo presentation.

After a routed issue is resolved, the item returns through `revised` and
`pending_review`; no role may directly mark it `approved` without
cross-review.
