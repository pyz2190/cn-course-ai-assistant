import json
from pathlib import Path

from scripts.evaluate import (
    AdapterResponse,
    RagRequest,
    RuntimeParameters,
    _git_commit,
    run_evaluation,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_DIRECTORY = PROJECT_ROOT / "evaluation"
JSONL_FILES = (
    "question_bank.jsonl",
    "annotations.jsonl",
    "evaluation_set.jsonl",
)


class RecordingAdapter:
    def answer(
        self,
        item: RagRequest,
        runtime: RuntimeParameters,
    ) -> AdapterResponse:
        del runtime
        return AdapterResponse(
            generated_answer=f"answer for {item.evaluation_id}",
            citations=[{"source": "test-adapter"}],
        )


class PartiallyFailingAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def answer(
        self,
        item: RagRequest,
        runtime: RuntimeParameters,
    ) -> AdapterResponse:
        del item, runtime
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("simulated adapter failure")
        return AdapterResponse(generated_answer="second answer", citations=[])


def _copy_evaluation_data(tmp_path: Path) -> Path:
    for name in JSONL_FILES:
        (tmp_path / name).write_text(
            (EVALUATION_DIRECTORY / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return tmp_path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _approved_evaluation_data(tmp_path: Path, count: int = 1) -> Path:
    directory = _copy_evaluation_data(tmp_path)
    questions = _load_jsonl(directory / "question_bank.jsonl")[:count]
    annotations = _load_jsonl(directory / "annotations.jsonl")[:count]
    for annotation in annotations:
        annotation.update(
            {
                "review_status": "approved",
                "reviewer": "reviewer-1",
                "reviewed_at": "2026-08-03T00:00:00Z",
                "expected_citations": [
                    {
                        "resource_id": "course-resource-001",
                        "chunk_id": "course-chunk-001",
                    }
                ],
            }
        )
    _write_jsonl(directory / "annotations.jsonl", annotations)
    _write_jsonl(directory / "evaluation_set.jsonl", questions)
    return directory


def test_empty_evaluation_set_has_no_executable_items(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)

    run = run_evaluation(directory, tmp_path / "reports")

    assert run.exit_code == 0
    assert run.planned_evaluation_ids == []
    assert run.report_path is None
    assert run.results == []


def test_dry_run_validates_plan_without_creating_report(tmp_path: Path) -> None:
    directory = _approved_evaluation_data(tmp_path)

    run = run_evaluation(directory, tmp_path / "reports", dry_run=True)

    assert run.exit_code == 0
    assert run.planned_evaluation_ids == ["QA-CONCEPT-001"]
    assert run.report_path is None
    assert not (tmp_path / "reports").exists()


def test_invalid_evaluation_data_stops_before_execution(tmp_path: Path) -> None:
    directory = _copy_evaluation_data(tmp_path)
    evaluation_set = directory / "evaluation_set.jsonl"
    evaluation_set.write_text("{invalid json}\n", encoding="utf-8")

    run = run_evaluation(directory, tmp_path / "reports", dry_run=True)

    assert run.exit_code == 1
    assert any("invalid JSON" in issue.reason for issue in run.data_issues)
    assert run.report_path is None


def test_execution_continues_after_single_adapter_failure(tmp_path: Path) -> None:
    directory = _approved_evaluation_data(tmp_path, count=2)

    run = run_evaluation(
        directory,
        tmp_path / "reports",
        adapter=PartiallyFailingAdapter(),
    )

    assert run.exit_code == 2
    assert len(run.results) == 2
    assert run.results[0]["generated_answer"] == ""
    assert "simulated adapter failure" in run.results[0]["error"]
    assert run.results[1]["generated_answer"] == "second answer"
    assert run.report_path is not None


def test_execution_report_contains_required_fields(tmp_path: Path) -> None:
    directory = _approved_evaluation_data(tmp_path)

    run = run_evaluation(
        directory,
        tmp_path / "reports",
        adapter=RecordingAdapter(),
        model="test-model",
        top_k=3,
    )

    assert run.exit_code == 0
    assert run.report_path is not None
    record = _load_jsonl(run.report_path)[0]
    assert set(record) == {
        "run_id",
        "evaluation_id",
        "generated_answer",
        "citations",
        "scores",
        "error",
        "runtime",
    }
    assert record["run_id"].startswith("RUN-")
    assert record["runtime"]["git_commit"] == _git_commit()
    assert record["runtime"]["model"] == "test-model"
    assert record["runtime"]["top_k"] == 3


def test_unconfigured_adapter_does_not_fabricate_answer(tmp_path: Path) -> None:
    directory = _approved_evaluation_data(tmp_path)

    run = run_evaluation(directory, tmp_path / "reports")

    assert run.exit_code == 2
    assert run.results[0]["generated_answer"] == ""
    assert run.results[0]["citations"] == []
    assert "NotImplementedError" in run.results[0]["error"]


def test_adapter_request_does_not_include_evaluation_references(tmp_path: Path) -> None:
    directory = _approved_evaluation_data(tmp_path)

    class RequestInspectingAdapter:
        def answer(
            self,
            item: RagRequest,
            runtime: RuntimeParameters,
        ) -> AdapterResponse:
            del runtime
            assert item.evaluation_id == "QA-CONCEPT-001"
            assert item.question
            assert item.knowledge_point_ids
            assert not hasattr(item, "expected_answer")
            assert not hasattr(item, "key_points")
            return AdapterResponse(generated_answer="sanitized request", citations=[])

    run = run_evaluation(directory, tmp_path / "reports", adapter=RequestInspectingAdapter())

    assert run.exit_code == 0
