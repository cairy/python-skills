# image-tools

当用户需要对本地图片进行标准化预处理（方向校正、等比缩放、格式转换、压缩、批量处理、画框标注）时使用本工具；不提供图片编辑、OCR、网络下载、视频处理。

## 功能介绍

- **方向校正**：自动读取 EXIF Orientation 并转正图片
- **等比缩放**：fit-without-pad 模式保持宽高比
- **格式转换**：JPG / PNG / WebP
- **压缩**：同格式重新编码，调整 JPEG/WebP quality
- **批量处理**：递归处理目录，失败自动跳过并记录日志
- **画框标注**：在图片上绘制矩形框用于调试

## 安装方式

```bash
pip install -e .
```

## 快速使用

```bash
# 标准化单张图片
python3 scripts/main.py normalize input.png --width 1024 --height 1024 --output out.jpg

# 自定义 pipeline
python3 scripts/main.py process input.jpg --pipeline "compress" --quality 60 --output out.jpg

# 批量处理
python3 scripts/main.py process \
  --input-dir ./photos \
  --output-dir ./processed \
  --pipeline "exif-transpose,resize,convert" \
  --width 1024 --height 1024 --format jpg
```

## 参数说明

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
|------|------|----------|--------|------|
| `input` | str | 单文件必填 | - | 输入图片路径 |
| `--output` / `-o` | str | 单文件必填 | - | 输出图片路径 |
| `--input-dir` | str | 批量必填 | - | 输入目录 |
| `--output-dir` | str | 批量必填 | - | 输出目录 |
| `--pipeline` | str | process 必填 | - | 逗号分隔原子操作 |
| `--width` | int | resize 必填 | - | 目标宽度上限 |
| `--height` | int | resize 必填 | - | 目标高度上限 |
| `--format` | str | 否 | jpg | jpg/png/webp |
| `--quality` | int | 否 | 85 | 1-100 |
| `--keep-exif` | flag | 否 | false | 保留 EXIF |

## 异常说明

| 异常类型 | 触发条件 | 处理建议 |
|----------|----------|----------|
| FileNotFoundError | 输入文件不存在 | 检查路径 |
| ValueError | 参数缺失/非法 | 查看 --help |
| PermissionError | 无读写权限 | 检查目录权限 |

## 测试

```bash
pytest
```
