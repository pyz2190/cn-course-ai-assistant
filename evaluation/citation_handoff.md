# Evaluation Citation Handoff

> Status: Awaiting Member B Evidence Delivery

## Required Delivery Fields

Member B must provide one verifiable citation record for each supported
answer-to-evidence relationship. A delivery includes all of the following:

- `evaluation_id`
- `resource_id`
- Resource title or file name
- `chunk_id`
- The Chunk's original text or a verifiable summary with a repository location
- The related knowledge point ID
- The specific `key_points` that the Chunk supports
- Chapter and page range, when the source provides them
- The resource's repository path

Providing only a `resource_id` and `chunk_id` is not a completed delivery. The
reviewer must be able to inspect the resource, confirm that the Chunk belongs to
it, and see how its content directly supports the listed answer points.

## Evidence Gaps by Evaluation Item

All 30 items are currently `pending_review`. There is no formal citation candidate
for any item: existing mock and example data are not eligible as course
evidence. The responsible role for every gap is Member B; the specific person
is **待确认**.

### QA-CONCEPT-001

- Required topic: longest-prefix matching, address specificity, and subnet
  route precedence.
- Required support: all three key points on selecting the longest prefix and
  preferring the more specific subnet route.
- Candidate: none eligible for formal use.
- Missing: a real resource, a belonging Chunk, and inspectable source text.

### QA-CONCEPT-002

- Required topic: Reno's loss-driven signals and BBR's bandwidth-delay model.
- Required support: the distinct control signals and their control goals.
- Candidate: none eligible for formal use.
- Missing: a real resource, a belonging Chunk, and inspectable source text.

### QA-PROTOCOL-001

- Required topic: the purpose of the TCP three-way handshake.
- Required support: initial sequence-number synchronization and confirmation of
  bidirectional send and receive capability.
- Candidate: none eligible for formal use.
- Missing: a real resource, a belonging Chunk, and inspectable source text.

### QA-PROTOCOL-002

- Required topic: the SYN, SYN-ACK, ACK sequence in a TCP handshake.
- Required support: the three-message order and the need to verify packet
  numbering and ordering.
- Candidate: none eligible for formal use.
- Missing: a real resource, a belonging Chunk, and inspectable source text.

### QA-TOOL-001

- Required topic: preparing a Wireshark handshake analysis and locating the
  three message types.
- Required support: preparation, packet location and annotation, and order
  verification before submission.
- Candidate: none eligible for formal use.
- Missing: a real course tool guide or lab material, a belonging Chunk, and
  inspectable source text.

### QA-TOOL-002

- Required topic: completion criteria and pre-submission checks for a
  Wireshark handshake analysis.
- Required support: labelled packet numbers, sequence verification, and
  returning to the capture when the result is inconsistent.
- Candidate: none eligible for formal use.
- Missing: a real course tool guide or lab material, a belonging Chunk, and
  inspectable source text.

### QA-LAB-001

- Required topic: TCP three-way-handshake capture experiment design.
- Required support: experiment objective, procedure, expected observation, and
  result judgement.
- Candidate: none eligible for formal use.
- Missing: a real lab guide, a belonging Chunk, and inspectable source text.

### QA-LAB-002

- Required topic: DNS resolution-failure troubleshooting with captures and
  configuration fragments.
- Required support: locating the failure, recording root-cause evidence, and
  verifying the repair.
- Candidate: none eligible for formal use.
- Missing: a real DNS lab guide or diagnostic material, a belonging Chunk, and
  inspectable source text.

### QA-ERROR-001

- Required topic: address-conflict diagnosis in a network design.
- Required support: locating duplicate assignments, correcting the plan, and
  verifying the result against the topology and address table.
- Candidate: none eligible for formal use.
- Missing: a real network-design resource, a belonging Chunk, and inspectable
  source text.

### QA-ERROR-002

- Required topic: correcting an unexpected TCP handshake packet order.
- Required support: returning to capture evidence, checking message type and
  number, correcting annotations, and rechecking the full sequence.
- Candidate: none eligible for formal use.
- Missing: a real capture-analysis resource, a belonging Chunk, and
  inspectable source text.

### QA-REVIEW-001

- Required topic: integrated topology, addressing, routing, security-boundary,
  address-conflict, and single-point-of-failure review.
- Required support: topology and subnet correspondence, longest-prefix route
  selection, and the three design checks.
- Candidate: none eligible for formal use.
- Missing: real network-design and addressing materials, belonging Chunks, and
  inspectable source text.

### QA-REVIEW-002

- Required topic: distinguishing Reno and BBR congestion-control analysis from
  edge load-balancing analysis.
- Required support: the two congestion-control signals, latency and failover
  concerns, and the separation of transport control from service assignment.
- Candidate: none eligible for formal use.
- Missing: real congestion-control and load-balancing materials, belonging
  Chunks, and inspectable source text.

### QA-CONCEPT-003

- Required topic: IP addressing, subnets, route-table entries, and longest-prefix
  route selection.
- Required support: the role of each element and its relation during a route
  lookup.
- Candidate: none eligible for formal use.
- Missing: a real addressing resource, a belonging Chunk, and inspectable
  source text.

### QA-CONCEPT-004

- Required topic: TCP handshake packet roles and initial sequence-number
  synchronization.
- Required support: packet classes, sequence-number observations, and why both
  are required for analysis.
- Candidate: none eligible for formal use.
- Missing: a real TCP teaching resource, a belonging Chunk, and inspectable
  source text.

### QA-CONCEPT-005

- Required topic: edge load balancing, latency, and failover.
- Required support: the two strategy objectives and the need to express their
  trade-off.
- Candidate: none eligible for formal use.
- Missing: a real edge-computing or load-balancing resource, a belonging Chunk,
  and inspectable source text.

### QA-PROTOCOL-003

- Required topic: the SYN, SYN-ACK, and ACK roles in the TCP handshake.
- Required support: initiation, both acknowledgements, initial sequence numbers,
  and bidirectional synchronization.
- Candidate: none eligible for formal use.
- Missing: a real TCP protocol resource, a belonging Chunk, and inspectable
  source text.

### QA-PROTOCOL-004

- Required topic: initial sequence-number synchronization in a TCP handshake.
- Required support: both endpoints supplying sequence numbers and subsequent
  acknowledgements confirming receipt.
- Candidate: none eligible for formal use.
- Missing: a real TCP protocol resource, a belonging Chunk, and inspectable
  source text.

### QA-PROTOCOL-005

- Required topic: DNS resolution troubleshooting through packet capture and
  configuration evidence.
- Required support: locating a failing stage, correlating it with configuration,
  and withholding a root-cause conclusion when evidence disagrees.
- Candidate: none eligible for formal use.
- Missing: a real DNS diagnostic resource, a belonging Chunk, and inspectable
  source text.

### QA-TOOL-003

- Required topic: recording TCP handshake packet numbers and sequence-number
  observations in Wireshark.
- Required support: three packet records, their sequence-number observations,
  and an order-and-synchronization review.
- Candidate: none eligible for formal use.
- Missing: a real Wireshark guide or lab material, a belonging Chunk, and
  inspectable source text.

### QA-TOOL-004

- Required topic: recording DNS troubleshooting evidence from captures and
  configuration fragments.
- Required support: a per-step observation, configuration evidence, judgement,
  repair action, and verification record.
- Candidate: none eligible for formal use.
- Missing: a real DNS troubleshooting guide, a belonging Chunk, and inspectable
  source text.

### QA-TOOL-005

- Required topic: organizing a Reno-versus-BBR comparison.
- Required support: each mechanism's control signal, its control goal, and a
  check against conflating both mechanisms as loss-driven.
- Candidate: none eligible for formal use.
- Missing: a real congestion-control resource, a belonging Chunk, and
  inspectable source text.

### QA-LAB-003

- Required topic: smart-home network-design deliverables.
- Required support: topology, address plan, security boundary, and checks for
  address conflicts and single points of failure.
- Candidate: none eligible for formal use.
- Missing: a real network-design lab guide, a belonging Chunk, and inspectable
  source text.

### QA-LAB-004

- Required topic: an edge load-balancing experiment.
- Required support: the latency-and-failover goal, strategy structure, metrics,
  trade-offs, and scenario evaluation.
- Candidate: none eligible for formal use.
- Missing: a real edge-computing lab guide, a belonging Chunk, and inspectable
  source text.

### QA-LAB-005

- Required topic: a Reno-versus-BBR congestion-control comparison experiment.
- Required support: common comparison dimensions, each mechanism's signal and
  goal, and the completion criterion that distinguishes them.
- Candidate: none eligible for formal use.
- Missing: a real congestion-control lab or case-study resource, a belonging
  Chunk, and inspectable source text.

### QA-ERROR-003

- Required topic: resolving insufficient or conflicting DNS troubleshooting
  evidence.
- Required support: continuing the investigation, avoiding an unsupported root
  cause, and re-verifying after a repair.
- Candidate: none eligible for formal use.
- Missing: a real DNS troubleshooting resource, a belonging Chunk, and
  inspectable source text.

### QA-ERROR-004

- Required topic: identifying and correcting single points of failure in a
  smart-home network design.
- Required support: locating the dependency in a topology, describing the
  continuity impact, and revising then rechecking the design.
- Candidate: none eligible for formal use.
- Missing: a real network-design resource, a belonging Chunk, and inspectable
  source text.

### QA-ERROR-005

- Required topic: correcting a conflated Reno and BBR description.
- Required support: Reno's loss-driven signal, BBR's bandwidth-delay model, and
  the relationship between signals and control goals.
- Candidate: none eligible for formal use.
- Missing: a real congestion-control resource, a belonging Chunk, and
  inspectable source text.

### QA-REVIEW-003

- Required topic: reviewing a DNS troubleshooting report.
- Required support: evidence-based failure location, supported root cause,
  targeted repair, and post-repair verification.
- Candidate: none eligible for formal use.
- Missing: a real DNS diagnostic or lab resource, a belonging Chunk, and
  inspectable source text.

### QA-REVIEW-004

- Required topic: reviewing an edge load-balancing solution.
- Required support: strategy structure, metrics, trade-off explanation, and
  coverage of latency and failover scenarios.
- Candidate: none eligible for formal use.
- Missing: a real edge-computing or load-balancing resource, a belonging Chunk,
  and inspectable source text.

### QA-REVIEW-005

- Required topic: reviewing a Reno-versus-BBR comparison.
- Required support: separate signal descriptions, control goals, and the absence
  of a false shared loss-driven characterization.
- Candidate: none eligible for formal use.
- Missing: a real congestion-control resource, a belonging Chunk, and
  inspectable source text.

## Acceptance Rules

An evidence delivery is acceptable only when all of the following hold:

1. The resource and Chunk both exist in the repository, and the Chunk belongs
   to the stated resource.
2. The Chunk text directly supports the expected answer and the mapped
   `key_points`; a merely related topic is insufficient.
3. Chapter and page fields are provided when the source contains them; otherwise
   they remain empty rather than being inferred.
4. Mock data and contract examples are not formal course citations.
5. If no valid material is found, the item remains `pending_review` with
   `expected_citations: []` and an evidence-gap note.
6. Do not invent resource IDs, Chunk IDs, chapter names, page numbers, or source
   locations to satisfy this checklist.

## Processing After Delivery

1. Verify that each delivered resource and Chunk exists and that their relation
   is correct.
2. Add only validated records to the matching annotation's
   `expected_citations`.
3. Have a cross-reviewer compare the expected answer and `key_points` with the
   supplied citation text.
4. If the review passes, record the real `reviewer` and `reviewed_at` values.
5. Change the annotation to `approved` only after the citation and cross-review
   checks pass.
6. Add the matching EvaluationItem to `evaluation_set.jsonl` only after its
   annotation is `approved`.
