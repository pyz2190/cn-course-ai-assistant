from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate import run_evaluation  # noqa: E402
from scripts.generate_evaluation_report import generate_evaluation_report  # noqa: E402
from scripts.score_evaluation_run import apply_scores, prepare_score_file  # noqa: E402
from scripts.sync_evaluation_set import sync_evaluation_set  # noqa: E402
from scripts.validate_evaluation_data import validate_evaluation_data  # noqa: E402


def _print_stage(name: str) -> None:
    print(f"==> Stage: {name}")


def _run_validation(evaluation_directory: Path) -> int:
    _print_stage("validate")
    result = validate_evaluation_data(evaluation_directory)
    print(f"Question bank records: {result.question_count}")
    print(f"Annotation records: {result.annotation_count}")
    print(f"Evaluation set records: {result.evaluation_set_count}")
    if not result.issues:
        print("Validation passed.")
        return 0
    print(f"Validation failed with {len(result.issues)} issue(s):")
    for issue in result.issues:
        print(f"- {issue.format()}")
    return 1


def _run_sync(evaluation_directory: Path, *, dry_run: bool) -> int:
    validation_exit_code = _run_validation(evaluation_directory)
    if validation_exit_code:
        return validation_exit_code
    _print_stage("sync")
    result = sync_evaluation_set(evaluation_directory, dry_run=dry_run)
    print(result.message)
    if result.selected_ids:
        print("Selected evaluation IDs:")
        for evaluation_id in result.selected_ids:
            print(f"- {evaluation_id}")
    if result.exit_code == 0:
        suffix = " (dry-run; not written)" if dry_run else ""
        print(f"Evaluation set: {evaluation_directory / 'evaluation_set.jsonl'}{suffix}")
    return result.exit_code


def _run_evaluate(
    evaluation_directory: Path,
    reports_directory: Path | None,
    *,
    dry_run: bool,
    model: str | None,
    embedding: str | None,
    reranker: str | None,
    top_k: int | None,
) -> int:
    validation_exit_code = _run_validation(evaluation_directory)
    if validation_exit_code:
        return validation_exit_code
    _print_stage("evaluate")
    result = run_evaluation(
        evaluation_directory,
        reports_directory,
        dry_run=dry_run,
        model=model,
        embedding=embedding,
        reranker=reranker,
        top_k=top_k,
    )
    if result.data_issues:
        print(f"Evaluation failed with {len(result.data_issues)} issue(s):")
        for issue in result.data_issues:
            print(f"- {issue.format()}")
    elif not result.planned_evaluation_ids:
        print("No executable evaluation items.")
    elif dry_run:
        print("Dry run completed; no RAG adapter was called.")
    else:
        print(f"Executed items: {len(result.results)}")
    if result.report_path is not None:
        print(f"Result file: {result.report_path}")
    return result.exit_code


def _run_prepare_scores(
    run_file: Path,
    annotations_path: Path | None,
    score_file: Path | None,
) -> int:
    _print_stage("prepare-scores")
    result = prepare_score_file(
        run_file,
        annotations_path=annotations_path,
        score_file=score_file,
    )
    print(result.message)
    if result.output_path is not None:
        print(f"Score file: {result.output_path}")
    return result.exit_code


def _run_apply_scores(run_file: Path, score_file: Path) -> int:
    _print_stage("apply-scores")
    result = apply_scores(run_file, score_file)
    print(result.message)
    if result.output_path is not None:
        print(f"Scored run file: {result.output_path}")
    return result.exit_code


def _run_report(
    run_file: Path,
    question_bank_path: Path | None,
    output_path: Path | None,
) -> int:
    _print_stage("report")
    result = generate_evaluation_report(
        run_file,
        question_bank_path=question_bank_path,
        output_path=output_path,
    )
    print(result.message)
    if result.output_path is not None:
        print(f"Baseline report: {result.output_path}")
    return result.exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run evaluation pipeline stages.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")
    sync_parser.add_argument("--dry-run", action="store_true")

    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--evaluation-dir", type=Path, default=ROOT / "evaluation")
    evaluate_parser.add_argument("--reports-dir", type=Path, default=None)
    evaluate_parser.add_argument("--dry-run", action="store_true")
    evaluate_parser.add_argument("--model", default=None)
    evaluate_parser.add_argument("--embedding", default=None)
    evaluate_parser.add_argument("--reranker", default=None)
    evaluate_parser.add_argument("--top-k", type=int, default=None)

    prepare_parser = subparsers.add_parser("prepare-scores")
    prepare_parser.add_argument("--run-file", type=Path, required=True)
    prepare_parser.add_argument("--annotations", type=Path, default=None)
    prepare_parser.add_argument("--score-file", type=Path, default=None)

    apply_parser = subparsers.add_parser("apply-scores")
    apply_parser.add_argument("--run-file", type=Path, required=True)
    apply_parser.add_argument("--score-file", type=Path, required=True)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--run-file", type=Path, required=True)
    report_parser.add_argument("--question-bank", type=Path, default=None)
    report_parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        return _run_validation(args.evaluation_dir)
    if args.command == "sync":
        return _run_sync(args.evaluation_dir, dry_run=args.dry_run)
    if args.command == "evaluate":
        return _run_evaluate(
            args.evaluation_dir,
            args.reports_dir,
            dry_run=args.dry_run,
            model=args.model,
            embedding=args.embedding,
            reranker=args.reranker,
            top_k=args.top_k,
        )
    if args.command == "prepare-scores":
        return _run_prepare_scores(args.run_file, args.annotations, args.score_file)
    if args.command == "apply-scores":
        return _run_apply_scores(args.run_file, args.score_file)
    return _run_report(args.run_file, args.question_bank, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
