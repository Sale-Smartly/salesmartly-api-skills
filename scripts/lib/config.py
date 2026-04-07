"""统一配置加载，兼容所有现有脚本的配置模式"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .exceptions import ConfigError


@dataclass
class Config:
    api_key: str
    project_id: str
    base_url: str = "https://developer.salesmartly.com"
    dingtalk_webhook: Optional[str] = None


def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = "SALESMARTLY",
) -> Config:
    """
    加载配置。优先级：环境变量 > 文件。

    文件搜索顺序（config_path 为空时）:
      1. CWD/api-key.json
      2. 脚本所在目录的父目录/api-key.json

    支持两种文件格式:
      - 平铺: {"apiKey": "...", "projectId": "..."}
      - 嵌套: {"salesmartly": {"apiKey": "...", "projectId": "..."}}

    环境变量（叠加覆盖文件值）:
      SALESMARTLY_API_KEY, SALESMARTLY_PROJECT_ID,
      SALESMARTLY_BASE_URL, SALESMARTLY_DINGTALK_WEBHOOK

    Raises:
        ConfigError: 无法找到 apiKey 或 projectId
    """
    api_key = None
    project_id = None
    base_url = "https://developer.salesmartly.com"
    dingtalk_webhook = None

    # --- 从文件加载 ---
    file_path = _resolve_config_path(config_path)
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件 JSON 格式错误：{e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败：{e}")

        # 支持嵌套格式
        if "salesmartly" in raw:
            nested = raw["salesmartly"]
            api_key = nested.get("apiKey")
            project_id = nested.get("projectId")
        else:
            api_key = raw.get("apiKey")
            project_id = raw.get("projectId")

        if raw.get("baseUrl"):
            base_url = raw["baseUrl"]

        dt = raw.get("dingtalk", {})
        if isinstance(dt, dict) and dt.get("webhook"):
            dingtalk_webhook = dt["webhook"]

    # --- 环境变量覆盖 ---
    env_key = os.environ.get(f"{env_prefix}_API_KEY")
    env_pid = os.environ.get(f"{env_prefix}_PROJECT_ID")
    env_url = os.environ.get(f"{env_prefix}_BASE_URL")
    env_dt = os.environ.get(f"{env_prefix}_DINGTALK_WEBHOOK")

    if env_key:
        api_key = env_key
    if env_pid:
        project_id = env_pid
    if env_url:
        base_url = env_url
    if env_dt:
        dingtalk_webhook = env_dt

    # --- 校验 ---
    if not api_key or not project_id:
        raise ConfigError(
            "缺少 apiKey 或 projectId。"
            "请在 api-key.json 中配置，或设置环境变量 "
            f"{env_prefix}_API_KEY / {env_prefix}_PROJECT_ID"
        )

    return Config(
        api_key=api_key,
        project_id=project_id,
        base_url=base_url,
        dingtalk_webhook=dingtalk_webhook,
    )


def _resolve_config_path(explicit: Optional[str]) -> Optional[str]:
    """按优先级查找配置文件，找不到返回 None"""
    if explicit:
        p = Path(explicit)
        if p.exists():
            return str(p)
        raise ConfigError(f"配置文件不存在：{explicit}")

    # CWD
    cwd = Path("api-key.json")
    if cwd.exists():
        return str(cwd)

    # 脚本目录的父目录（scripts/ -> 项目根目录）
    script_parent = Path(__file__).resolve().parent.parent.parent / "api-key.json"
    if script_parent.exists():
        return str(script_parent)

    return None
