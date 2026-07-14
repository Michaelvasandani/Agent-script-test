import json
import subprocess
import sys
from pathlib import Path

from scripts.analyze_repository import analyze_repository


def test_analyze_repository_returns_expected_statistics(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n\nHello\n", encoding="utf-8")
    package = tmp_path / "package"
    package.mkdir()
    (package / "example.py").write_text("print('hello')\n", encoding="utf-8")
    (package / "data.json").write_text('{"ok": true}\n', encoding="utf-8")

    result = analyze_repository(tmp_path)

    assert result == {
        "execution_confirmed": True,
        "script": "scripts/analyze_repository.py",
        "schema_version": 1,
        "statistics": {
            "files_by_extension": {".json": 1, ".md": 1, ".py": 1},
            "python_files": 1,
            "text_lines": 5,
            "total_directories": 1,
            "total_files": 3,
        },
    }


def test_analyze_repository_excludes_git_metadata(tmp_path: Path) -> None:
    git_directory = tmp_path / ".git" / "objects"
    git_directory.mkdir(parents=True)
    (git_directory / "internal.txt").write_text("not repository content\n", encoding="utf-8")
    (tmp_path / "tracked.txt").write_text("repository content\n", encoding="utf-8")

    result = analyze_repository(tmp_path)

    assert result["statistics"]["total_files"] == 1
    assert result["statistics"]["total_directories"] == 0
    assert result["statistics"]["files_by_extension"] == {".txt": 1}


def test_analyze_repository_excludes_generated_directories(tmp_path: Path) -> None:
    for directory_name in ("__pycache__", ".pytest_cache", ".venv"):
        generated_directory = tmp_path / directory_name
        generated_directory.mkdir()
        (generated_directory / "generated.pyc").write_bytes(b"generated")
    (tmp_path / "source.py").write_text("value = 1\n", encoding="utf-8")

    result = analyze_repository(tmp_path)

    assert result["statistics"]["total_files"] == 1
    assert result["statistics"]["total_directories"] == 0
    assert result["statistics"]["files_by_extension"] == {".py": 1}


def test_cli_prints_json_for_requested_repository(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("first = 1\nsecond = 2\n", encoding="utf-8")
    script = Path(__file__).parents[1] / "scripts" / "analyze_repository.py"

    completed = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["execution_confirmed"] is True
    assert result["statistics"]["python_files"] == 1
    assert result["statistics"]["text_lines"] == 2
