# Evaluation Scoring Rules

> Status: Draft

## Scope

These rules evaluate an answer against its `EvaluationItem` and the matching
`EvaluationAnnotation`. The annotation's `key_points` are the review
checklist, not a mechanical point-counting formula. Reviewers must consider
whether the answer reaches the requested conclusion, uses a sound explanation,
and covers the material points that make the answer usable for the question.

## Correctness

Score correctness on a 0–4 scale.

| Score | Definition |
| ---: | --- |
| 4 | The conclusion is correct and all material key points are covered. |
| 3 | The core conclusion is correct, with only minor secondary omissions. |
| 2 | The answer is partly correct but misses an important key point. |
| 1 | Only a small amount is correct and the main conclusion is wrong. |
| 0 | The answer is wrong, irrelevant, or absent. |

Use `key_points` to identify material requirements, then judge their accuracy
and relevance in context. Do not assign a score by simply dividing the number
of mentioned key points by the total: an answer can mention a key point while
explaining it incorrectly, and a missing decisive point can prevent a score of
3 or 4.

## Citation Accuracy

Score citation accuracy on a 0–4 scale only when the annotation provides an
evaluable citation expectation.

| Score | Definition |
| ---: | --- |
| 4 | Citations are complete and directly support the conclusions. |
| 3 | Main citations are correct, with only minor coverage or location issues. |
| 2 | Only part of the citations are effective support. |
| 1 | Most citations do not support the answer. |
| 0 | Citations are absent when required, incorrect, or irrelevant. |

`expected_citations: []` means **temporarily not evaluable** (`暂不可评`), not
a score of 0. Record the metric as unavailable and exclude it from any future
aggregate until a reviewer can compare the answer with real, verifiable source
locations. The current W1 annotations all use this state and must not be
penalized merely because member B has not supplied source and Chunk locations.

## Hallucination Rate

The hallucination rate is a value from 0.0 to 1.0:

```text
unsupported factual claims / all factual claims
```

Split an answer into independently checkable factual claims before counting.
Treat each asserted definition, mechanism, causal relation, procedure outcome,
number, or source attribution as a factual claim. Split conjunctions when the
connected parts can be verified separately. Do not count formatting, an
explicitly labelled uncertainty, or a purely evaluative statement without a
factual assertion.

Example answer: “TCP 三次握手同步初始序列号，确认双向收发能力，并在握手阶段自动加密全部业务数据。”
This contains three factual claims. If the first two are supported by the
reviewed material and the encryption claim is not, the hallucination rate is
`1 / 3 ≈ 0.33`.

When an answer contains no factual claim, record the rate as `暂不可评` rather
than dividing by zero. Reviewers should retain the claim split and the support
decision in review evidence so that the rate can be reproduced.

## Aggregation

No total-score formula is defined at this stage. Weighting correctness,
citation accuracy, and hallucination rate is **待组内确认**. Do not infer a
total score from these rules or use a total score as a condition for approval
before that decision is recorded.
