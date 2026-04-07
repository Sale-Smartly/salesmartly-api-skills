"""SaleSmartly API 异常类"""


class SaleSmartlyError(Exception):
    """所有 SaleSmartly 错误的基类"""
    pass


class ConfigError(SaleSmartlyError):
    """配置缺失或无效"""
    pass


class APIError(SaleSmartlyError):
    """API 返回非零 code"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API 错误 {code}: {message}")


class NetworkError(SaleSmartlyError):
    """HTTP/SSL/超时错误"""
    pass
