"""统一输出格式化，支持 emoji 和 JSON 两种模式"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


def add_output_args(parser) -> None:
    """给 argparse parser 添加 --json / --quiet / --config 参数"""
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--quiet", action="store_true", help="安静模式，最少输出")
    parser.add_argument(
        "--config", type=str, default=None, help="配置文件路径（默认 api-key.json）"
    )


def print_result(
    success: bool,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    error_msg: Optional[str] = None,
    error_code: Optional[int] = None,
    json_mode: bool = False,
) -> None:
    """
    统一输出结果。

    JSON 模式输出:
        {"success": true, "data": ..., "meta": {...}}
        {"success": false, "error": {"code": N, "message": "..."}}

    普通模式输出:
        ✅ 或 ❌ 前缀的人类可读文本
    """
    if json_mode:
        result: Dict[str, Any] = {"success": success}
        if success:
            if data is not None:
                result["data"] = data
            if meta:
                result["meta"] = meta
        else:
            result["error"] = {
                "code": error_code or -1,
                "message": error_msg or "Unknown error",
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not success:
            print(f"❌ {error_msg or 'Unknown error'}")


def print_table(
    headers: List[str],
    rows: List[List[Any]],
    json_mode: bool = False,
) -> None:
    """
    输出表格数据。

    JSON 模式：输出 dict 数组。
    普通模式：对齐的文本表格。
    """
    if json_mode:
        items = [dict(zip(headers, row)) for row in rows]
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not rows:
        print("（无数据）")
        return

    # 计算列宽
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # 打印表头
    header_line = "  ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    # 打印行
    for row in rows:
        print("  ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))


def format_timestamp(ts: Any) -> str:
    """
    将 10 位或 13 位时间戳转为 YYYY-MM-DD HH:MM:SS。
    无效值返回 'N/A'。
    """
    if ts is None:
        return "N/A"
    try:
        ts = int(ts)
        if ts > 1_000_000_000_000:
            ts = ts // 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return "N/A"
