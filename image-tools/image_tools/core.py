"""image-tools 共享基础设施：类型定义、校验、工具函数。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ImageFormat = Literal["jpg", "jpeg", "png", "webp"]
"""支持的输出图片格式。"""

ResizeMode = Literal["fit", "cover", "fit-without-pad"]
"""支持的缩放模式。"""

PipelineStep = Literal[
    "exif-transpose",
    "resize",
    "convert",
    "compress",
    "annotate",
]
"""支持的原子操作名称。"""


@dataclass
class Box:
    """图片上的矩形标注框。

    坐标基于左上角原点，x 向右增长，y 向下增长。
    """

    x: int
    y: int
    width: int
    height: int
    name: str = ""
    color: str = ""

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("width and height must be >= 0")

@dataclass
class ProcessResult:
    """单张图片处理结果。"""

    input_path: str
    output_path: str
    width: int
    height: int
    format: str
    size_bytes: int


@dataclass
class BatchResult:
    """批量目录处理结果。"""

    success_count: int
    failure_count: int
    output_dir: str
    log_path: str


def validate_input_path(path: str | Path) -> Path:
    """校验输入路径存在且可读。

    Args:
        path: 输入文件路径。

    Returns:
        Path: 校验后的路径对象。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 路径不是文件。
        PermissionError: 无读取权限。
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在：{path_obj}")
    if not path_obj.is_file():
        raise ValueError(f"路径不是文件：{path_obj}")
    if not os.access(path_obj, os.R_OK):
        raise PermissionError(f"无读取权限：{path_obj}")
    return path_obj


def validate_output_dir(path: str | Path) -> Path:
    """校验输出目录存在或可创建。

    Args:
        path: 输出目录路径。

    Returns:
        Path: 校验后的目录路径对象。

    Raises:
        ValueError: 输出路径已存在但不是目录。
        PermissionError: 输出目录无写入权限。
    """
    path_obj = Path(path)
    if path_obj.exists() and not path_obj.is_dir():
        raise ValueError(f"输出路径已存在但不是目录：{path_obj}")
    if not path_obj.exists():
        path_obj.mkdir(parents=True, exist_ok=True)
    if not os.access(path_obj, os.W_OK):
        raise PermissionError(f"输出目录无写入权限：{path_obj}")
    return path_obj
