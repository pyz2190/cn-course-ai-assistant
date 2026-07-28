from __future__ import annotations

import filecmp
import tempfile
from pathlib import Path

from export_contracts import ROOT, export_contracts


def _generated_json_files(path: Path) -> set[Path]:
    files = {Path("openapi.json")} if (path / "openapi.json").is_file() else set()
    schemas = path / "schemas"
    if schemas.is_dir():
        files.update(item.relative_to(path) for item in schemas.rglob("*.json"))
    return files


def main() -> int:
    expected = ROOT / "contracts"
    with tempfile.TemporaryDirectory(prefix="cn-ai-contracts-") as temp_dir:
        generated = export_contracts(Path(temp_dir))
        expected_files = _generated_json_files(expected)
        generated_files = _generated_json_files(generated)
        if expected_files != generated_files:
            print("Contract file set is stale.")
            print(f"Expected: {sorted(map(str, expected_files))}")
            print(f"Generated: {sorted(map(str, generated_files))}")
            return 1

        changed = [
            relative
            for relative in sorted(expected_files)
            if not filecmp.cmp(expected / relative, generated / relative, shallow=False)
        ]
        if changed:
            print("Generated contracts differ:")
            for relative in changed:
                print(f"- {relative}")
            return 1

    print("Contracts are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
