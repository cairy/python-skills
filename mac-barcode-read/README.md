# mac-barcode-read

在 macOS 上读取单张本地图片中的条码，输出稳定 JSON 协议。

## 功能说明
- 输入单张图片路径，返回 `success/data` 结构。
- `data.codes` 为条码数组，字段统一为 `value`、`barcode_type`、`bbox`、`confidence`。
- 无识别结果时返回空数组，仍为成功响应。

## 码制可用性策略
- 默认不传 `--barcode-type` 时，使用内置默认集合；若系统不支持其中部分码制，会自动降级为可用子集继续执行。
- 显式传入 `--barcode-type` 时，若包含当前系统不可用码制，将立即报错并退出（退出码 `1`）。

## 安装
```bash
pip install -e .
```

安装会自动拉取 `pyobjc-core`、`pyobjc-framework-Cocoa`、`pyobjc-framework-Quartz`、`pyobjc-framework-Vision`，用于 `Vision/Foundation/Quartz` 运行时绑定。

## 命令行用法
```bash
python scripts/main.py --help
python scripts/main.py "./sample.png"
python scripts/main.py "./sample.png" --region 10,20,120,80 --barcode-type qrcode
```

## 输出协议
成功时 stdout 仅输出 JSON：

```json
{
  "success": true,
  "data": {
    "image_path": "/abs/path/sample.png",
    "codes": []
  }
}
```

失败时：
- stdout 不输出成功 JSON；
- stderr 输出错误文本与结构化错误 JSON；
- 退出码为 `1`。

## Python 调用示例
```python
from mac_barcode_read import build_success_payload, read_barcodes_from_image

result = read_barcodes_from_image("sample.png")
payload = build_success_payload(
    image_path=result["image_path"],
    codes=result["codes"],
)
print(payload)
```

## 测试
```bash
pytest tests/test_contract.py
```
