"""scripts/main.py CLI 测试。"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

MAIN_PY = Path(__file__).parent.parent / "scripts" / "main.py"


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """运行 CLI 并返回结果。"""
    cmd = [sys.executable, str(MAIN_PY)] + args
    return subprocess.run(cmd, capture_output=True, text=True)


class TestMetadataCommand:
    """测试 metadata 子命令。"""

    def test_metadata_success(self, sample_with_metadata_pdf: Path) -> None:
        result = run_cli(["metadata", str(sample_with_metadata_pdf)])
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert output["data"]["title"] == "Test Document"
        assert output["data"]["page_count"] == 1

    def test_metadata_file_not_found(self) -> None:
        result = run_cli(["metadata", "/tmp/nonexistent_xyz.pdf"])
        assert result.returncode == 1
        assert result.stderr != ""


class TestSplitCommand:
    """测试 split 子命令。"""

    def test_split_success(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "split_cli.pdf"
        result = run_cli([
            "split", str(sample_multi_page_pdf),
            "--ranges", "1-2",
            "--output", str(output),
        ])
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data["success"] is True
        assert output_data["data"] == str(output)
        assert output.exists()


class TestExtractTextCommand:
    """测试 extract-text 子命令。"""

    def test_extract_text_success(self, sample_single_page_pdf: Path) -> None:
        result = run_cli(["extract-text", str(sample_single_page_pdf)])
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "Hello PDF World" in output["data"]


class TestExtractTextBlocksCommand:
    """测试 extract-text-blocks 子命令。"""

    def test_extract_blocks_success(self, sample_single_page_pdf: Path) -> None:
        result = run_cli(["extract-text-blocks", str(sample_single_page_pdf)])
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert isinstance(output["data"], list)
        assert len(output["data"]) > 0
        assert "text" in output["data"][0]
        assert "x" in output["data"][0]
        assert "y" in output["data"][0]


class TestMergeCommand:
    """测试 merge 子命令。"""

    def test_merge_success(self, sample_single_page_pdf: Path, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "merged_cli.pdf"
        result = run_cli([
            "merge", str(sample_single_page_pdf), str(sample_multi_page_pdf),
            "--output", str(output),
        ])
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data["success"] is True
        assert output_data["data"] == str(output)
        assert output.exists()


class TestRotateCommand:
    """测试 rotate 子命令。"""

    def test_rotate_success(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "rotated_cli.pdf"
        result = run_cli([
            "rotate", str(sample_multi_page_pdf),
            "--pages", "1",
            "--angle", "90",
            "--output", str(output),
        ])
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data["success"] is True
        assert output_data["data"] == str(output)
        assert output.exists()


class TestExtractImagesCommand:
    """测试 extract-images 子命令。"""

    def test_extract_images_files_mode(self, sample_with_image_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "cli_images"
        result = run_cli([
            "extract-images", str(sample_with_image_pdf),
            "--output-mode", "files",
            "--output-dir", str(output_dir),
        ])
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert isinstance(output["data"], list)

    def test_extract_images_missing_output_dir(self, sample_with_image_pdf: Path) -> None:
        result = run_cli([
            "extract-images", str(sample_with_image_pdf),
            "--output-mode", "files",
        ])
        assert result.returncode == 1
        assert "output-dir" in result.stderr.lower() or "output_dir" in result.stderr.lower()


class TestErrorHandling:
    """测试错误处理和 JSON 输出。"""

    def test_error_json_structure(self) -> None:
        result = run_cli(["metadata", "/nonexistent_file_xyz.pdf"])
        assert result.returncode == 1
        assert '"success": false' in result.stderr
        assert "error" in result.stderr
        assert "error_type" in result.stderr
