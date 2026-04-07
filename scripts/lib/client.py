"""SaleSmartly API HTTP 客户端"""

import hashlib
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .config import Config
from .exceptions import APIError, NetworkError


class SaleSmartlyClient:
    """SaleSmartly API 客户端，封装签名、SSL、请求构建"""

    USER_AGENT = "SaleSmartly-Agent/1.0"

    def __init__(self, config: Config, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self._ssl_ctx = self._build_ssl_context()

    # ── 公开方法 ──────────────────────────────────────────

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
        """
        发送 GET 请求。

        - 自动注入 project_id
        - 自动对 JSON 字符串值做 URL 编码
        - 自动计算签名

        Returns:
            API 响应的 data 字段（dict）
        """
        params = self._inject_project_id(params)
        sign = self.generate_sign(self.config.api_key, params)

        # 构建 query string（JSON 值需要 URL 编码）
        query_parts = []
        for k, v in params.items():
            sv = str(v)
            if sv.startswith("{") or sv.startswith("["):
                query_parts.append(f"{k}={urllib.parse.quote(sv)}")
            else:
                query_parts.append(f"{k}={urllib.parse.quote(sv, safe='')}")
        query_string = "&".join(query_parts)

        url = f"{self.config.base_url}{endpoint}?{query_string}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.USER_AGENT,
            "External-Sign": sign,
        }

        req = urllib.request.Request(url, headers=headers)
        return self._execute(req)

    def post(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> dict:
        """
        发送 POST 请求（multipart/form-data）。

        - 自动注入 project_id
        - 自动计算签名

        Returns:
            API 响应的 data 字段（dict）
        """
        params = self._inject_project_id(params)
        sign = self.generate_sign(self.config.api_key, params)

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
        body_lines: list[str] = []
        for key, value in params.items():
            body_lines.append(f"--{boundary}")
            body_lines.append(f'Content-Disposition: form-data; name="{key}"')
            body_lines.append("")
            body_lines.append(str(value))
        body_lines.append(f"--{boundary}--")
        body_lines.append("")
        data = "\r\n".join(body_lines).encode("utf-8")

        url = f"{self.config.base_url}{endpoint}"
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": self.USER_AGENT,
            "External-Sign": sign,
        }

        req = urllib.request.Request(url, data=data, method="POST", headers=headers)
        return self._execute(req)

    def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: int = 100,
        list_key: str = "list",
    ) -> Tuple[List[dict], int]:
        """
        自动翻页获取所有数据。

        Returns:
            (all_items, total) — 所有记录列表和总数
        """
        params = dict(params or {})
        all_items: List[dict] = []
        total = 0

        for page in range(1, max_pages + 1):
            params["page"] = str(page)
            params["page_size"] = str(page_size)
            data = self.get(endpoint, params)
            total = data.get("total") or total
            items = data.get(list_key) or []
            if not items:
                break
            all_items.extend(items)
            if len(items) < page_size:
                break

        return all_items, total

    def post_webhook(self, url: str, payload: dict, timeout: int = 10) -> dict:
        """发送 JSON POST 到外部 webhook（如钉钉）"""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise NetworkError(f"Webhook 请求失败：{e}")

    # ── 签名 ──────────────────────────────────────────────

    @staticmethod
    def generate_sign(api_key: str, params: dict) -> str:
        """
        生成 MD5 签名。

        规则：apiKey 放最前，参数按 key 排序，用 & 拼接，MD5 取 32 位小写。
        None 值参数自动跳过（空字符串保留参与签名）。
        """
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_parts = [api_key]
        for k, v in sorted_params:
            if v is not None:
                sign_parts.append(f"{k}={v}")
        sign_str = "&".join(sign_parts)
        return hashlib.md5(sign_str.encode()).hexdigest()

    # ── 内部方法 ──────────────────────────────────────────

    def _inject_project_id(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        params = dict(params or {})
        params.setdefault("project_id", self.config.project_id)
        return params

    def _execute(self, req: urllib.request.Request) -> dict:
        """执行请求，解析响应，处理错误"""
        try:
            with urllib.request.urlopen(
                req, timeout=self.timeout, context=self._ssl_ctx
            ) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            raise NetworkError(f"HTTP 错误 {e.code}: {body}")
        except urllib.error.URLError as e:
            raise NetworkError(f"网络错误：{e.reason}")
        except Exception as e:
            raise NetworkError(f"请求失败：{e}")

        return self._check_response(resp_json)

    def _check_response(self, resp_json: dict) -> dict:
        """检查 API 响应 code，提取 data"""
        code = resp_json.get("code", -1)
        if code != 0:
            raise APIError(code, resp_json.get("msg", "Unknown error"))
        return resp_json.get("data", {})

    @staticmethod
    def _build_ssl_context() -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx
