# Evaluation Pipeline

Run the stages from the repository root in this order. Stop when a command
returns a non-zero exit code; do not create later artifacts from a failed
stage.

```bash
python scripts/run_evaluation_pipeline.py validate
python scripts/run_evaluation_pipeline.py sync --dry-run
python scripts/run_evaluation_pipeline.py sync
python scripts/run_evaluation_pipeline.py evaluate --dry-run
python scripts/run_evaluation_pipeline.py evaluate
python scripts/run_evaluation_pipeline.py prepare-scores \
  --run-file evaluation/reports/runs/<run_id>.jsonl
python scripts/run_evaluation_pipeline.py apply-scores \
  --run-file evaluation/reports/runs/<run_id>.jsonl \
  --score-file evaluation/reports/scores/<run_id>.jsonl
python scripts/run_evaluation_pipeline.py report \
  --run-file evaluation/reports/runs/<run_id>.scored.jsonl
```

## Stage Responsibilities

- `validate` reuses `validate_evaluation_data.py` and only reports validation.
- `sync` reuses `sync_evaluation_set.py` and writes the approved-only
  `evaluation_set.jsonl`.
- `evaluate` reuses `evaluate.py` and writes `reports/runs/<run_id>.jsonl`.
- `prepare-scores` reuses `score_evaluation_run.py prepare` and writes
  `scores/<run_id>.jsonl`.
- `apply-scores` reuses `score_evaluation_run.py apply` and writes
  `runs/<run_id>.scored.jsonl`.
- `report` reuses `generate_evaluation_report.py` and writes `baseline.md`.

`sync` and `evaluate` run validation first and stop if it fails. All other
commands validate their own inputs and return their originating script's exit
code without creating a replacement artifact after an error.

## Exit Codes

- `0`: The requested stage succeeded. An empty formal set and an evaluation
  dry-run with no items are successful no-op states.
- `1`: Data or input validation failed.
- `2`: A valid request could not produce its expected artifact, such as too few
  approved items, a missing run file, no valid scores, or an execution error.

## CI Checks

GitHub Actions uses the existing Python 3.11 setup and
`python -m pip install -e "apps/api[dev]"` dependency installation. Its
evaluation gate runs:

```bash
python scripts/run_evaluation_pipeline.py validate
python scripts/run_evaluation_pipeline.py sync --dry-run
python scripts/run_evaluation_pipeline.py evaluate --dry-run
pytest apps/api
ruff check apps/api scripts
```

The synchronization and evaluation commands are dry-runs, so CI does not alter
`evaluation_set.jsonl`, invoke a RAG adapter, create a run report, or create a
score file. An empty approved set is a successful CI state. Markdown lint is
not currently part of CI because `markdownlint-cli2` is not installed in the
Node dependency lockfile.

Member B's real citations and Member D's RAG adapter, credentials, and runtime
are not required by this gate. After those integrations are complete, add CI
checks for resource-to-Chunk validity, approved citation support, and an
authenticated adapter integration test using non-production fixtures.

## Current External Dependencies

- Member B: provide real, verifiable course resources and Chunk locations for
  `expected_citations`. Mock and example data cannot be used as formal
  citations.
- Member D: provide the configured RAG adapter invocation, authentication,
  runtime parameters, Citation mapping, timeout/retry behaviour, and test
  environment. Until then, `evaluate` must not fabricate answers or results.
