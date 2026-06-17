"""Tests for scripts/main.py CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "main.py"


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )


def test_help():
    result = run_cli(["--help"])
    assert result.returncode == 0
    assert "process" in result.stdout
    assert "normalize" in result.stdout


def test_process_normalize_success(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.jpg"

    result = run_cli([
        "normalize",
        str(input_path),
        "--output", str(output_path),
        "--width", "200",
        "--height", "200",
    ])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["width"] == 200
    assert data["data"]["height"] == 150
    assert output_path.exists()


def test_process_missing_input():
    result = run_cli(["process", "--pipeline", "resize"])
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Error" in result.stderr


def test_process_batch(tmp_path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    sample = Path("evals/files/sample_400x300.jpg").read_bytes()
    (input_dir / "a.jpg").write_bytes(sample)

    output_dir = tmp_path / "out"

    result = run_cli([
        "process",
        "--input-dir", str(input_dir),
        "--output-dir", str(output_dir),
        "--pipeline", "resize,convert",
        "--width", "200",
        "--height", "200",
        "--format", "png",
    ])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["data"]["success_count"] == 1
    assert (output_dir / "a.png").exists()


def test_process_compress(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.jpg"

    result = run_cli([
        "process",
        str(input_path),
        "--output", str(output_path),
        "--pipeline", "compress",
        "--quality", "30",
    ])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["format"] == "jpg"
    assert output_path.exists()


def test_process_annotate(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.jpg"

    result = run_cli([
        "process",
        str(input_path),
        "--output", str(output_path),
        "--pipeline", "annotate",
        "--box", "face,10,20,100,80,red",
    ])

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert output_path.exists()
