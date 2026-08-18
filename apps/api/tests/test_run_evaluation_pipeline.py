from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_evaluation_pipeline as pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_DIRECTORY = PROJECT_ROOT / "evaluation"


def _valid_validation_result() -> SimpleNamespace:
    return SimpleNamespace(
        issues=[],
        question_count=30,
        annotation_count=30,
        evaluation_set_count=0,
    )


def _stage_result(output_path: Path | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        exit_code=0,
        message="stage completed",
        selected_ids=[],
        output_path=output_path,
        data_issues=[],
        planned_evaluation_ids=[],
        report_path=output_path,
        results=[],
    )


def test_sync_forwards_dry_run_after_validation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, object] = {}

    def fake_sync(directory: Path, *, dry_run: bool) -> SimpleNamespace:
        calls["directory"] = directory
        calls["dry_run"] = dry_run
        return _stage_result()

    monkeypatch.setattr(pipeline, "validate_evaluation_data", lambda _: _valid_validation_result())
    monkeypatch.setattr(pipeline, "sync_evaluation_set", fake_sync)

    exit_code = pipeline.main(["sync", "--evaluation-dir", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    assert calls == {"directory": tmp_path, "dry_run": True}


def test_validation_failure_stops_sync(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Issue:
        def format(self) -> str:
            return "validation failed"

    invalid_result = SimpleNamespace(
        issues=[Issue()],
        question_count=0,
        annotation_count=0,
        evaluation_set_count=0,
    )
    monkeypatch.setattr(pipeline, "validate_evaluation_data", lambda _: invalid_result)
    monkeypatch.setattr(
        pipeline,
        "sync_evaluation_set",
        lambda *_args, **_kwargs: pytest.fail("sync must not run after validation failure"),
    )

    exit_code = pipeline.main(["sync", "--evaluation-dir", str(tmp_path)])

    assert exit_code == 1


def test_evaluate_forwards_dry_run_and_runtime_parameters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, object] = {}

    def fake_evaluate(
        directory: Path,
        reports_directory: Path | None,
        **kwargs: object,
    ) -> SimpleNamespace:
        calls["directory"] = directory
        calls["reports_directory"] = reports_directory
        calls.update(kwargs)
        return _stage_result()

    monkeypatch.setattr(pipeline, "validate_evaluation_data", lambda _: _valid_validation_result())
    monkeypatch.setattr(pipeline, "run_evaluation", fake_evaluate)

    exit_code = pipeline.main(
        [
            "evaluate",
            "--evaluation-dir",
            str(tmp_path),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--dry-run",
            "--model",
            "model-test",
            "--embedding",
            "embedding-test",
            "--reranker",
            "reranker-test",
            "--top-k",
            "7",
        ]
    )

    assert exit_code == 0
    assert calls == {
        "directory": tmp_path,
        "reports_directory": tmp_path / "reports",
        "dry_run": True,
        "model": "model-test",
        "embedding": "embedding-test",
        "reranker": "reranker-test",
        "top_k": 7,
    }


def test_score_and_report_commands_forward_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, tuple[object, ...]] = {}
    run_file = tmp_path / "run.jsonl"
    score_file = tmp_path / "scores.jsonl"
    output_path = tmp_path / "baseline.md"

    def fake_prepare(*args: object, **kwargs: object) -> SimpleNamespace:
        calls["prepare"] = (*args, kwargs)
        return _stage_result(tmp_path / "prepared.jsonl")

    def fake_apply(*args: object, **kwargs: object) -> SimpleNamespace:
        calls["apply"] = (*args, kwargs)
        return _stage_result(tmp_path / "scored.jsonl")

    def fake_report(*args: object, **kwargs: object) -> SimpleNamespace:
        calls["report"] = (*args, kwargs)
        return _stage_result(output_path)

    monkeypatch.setattr(pipeline, "prepare_score_file", fake_prepare)
    monkeypatch.setattr(pipeline, "apply_scores", fake_apply)
    monkeypatch.setattr(pipeline, "generate_evaluation_report", fake_report)

    assert pipeline.main(["prepare-scores", "--run-file", str(run_file)]) == 0
    assert pipeline.main(
        ["apply-scores", "--run-file", str(run_file), "--score-file", str(score_file)]
    ) == 0
    assert pipeline.main(
        ["report", "--run-file", str(run_file), "--output", str(output_path)]
    ) == 0
    assert calls["prepare"] == (run_file, {"annotations_path": None, "score_file": None})
    assert calls["apply"] == (run_file, score_file, {})
    assert calls["report"] == (
        run_file,
        {"question_bank_path": None, "output_path": output_path},
    )


def test_empty_formal_set_is_a_successful_evaluate_dry_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = pipeline.main(
        ["evaluate", "--evaluation-dir", str(EVALUATION_DIRECTORY), "--dry-run"]
    )

    assert exit_code == 0
    assert "No executable evaluation items." in capsys.readouterr().out


def test_missing_required_subcommand_parameter_is_rejected() -> None:
    with pytest.raises(SystemExit) as error:
        pipeline.main(["prepare-scores"])

    assert error.value.code == 2
