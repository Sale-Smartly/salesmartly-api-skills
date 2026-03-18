# SaleSmartly API 认证说明

## 🔐 签名规则

根据 [官方文档](https://help.salesmartly.com/docs/obtain-instructions-for-the-header-parameter-of-api)：

### 签名步骤

1. **Token 放在最前面**
2. **其他参数按字母顺序排序**（A-Z）
3. **用 `&` 连接** 所有参数（格式：`key=value`）
4. **MD5 加密**（32 位小写）

### Python 实现

```python
import hashlib

api_key = "AtGj4SbRIs7XCKt"
params = {
    "project_id": "f9m526",
    "page": "1",
    "page_size": "5",
    "updated_time": '{"start":1770540602,"end":1773132602}'
}

# 1. 参数按字母排序
sorted_params = sorted(params.items(), key=lambda x: x[0])

# 2. Token 放最前面，用 & 连接
sign_parts = [api_key]
for k, v in sorted_params:
    sign_parts.append(f"{k}={v}")
sign_str = "&".join(sign_parts)

# 3. MD5 加密（32 位小写）
sign = hashlib.md5(sign_str.encode()).hexdigest()
print(f"签名：{sign}")
```

### 示例

```
签名字符串：AtGj4SbRIs7XCKt&page=1&page_size=5&project_id=f9m526&updated_time={"start":1770540602,"end":1773132602}
MD5 签名：9e6c081465718670b907e544ad1ec98b
```

## 📡 请求头

```http
GET /api/v2/get-contact-list?project_id=f9m526&updated_time=...&page=1&page_size=5 HTTP/1.1
Host: developer.salesmartly.com
Content-Type: application/json
User-Agent: SaleSmartly-Agent/1.0
External-Sign: 9e6c081465718670b907e544ad1ec98b
```

## 🔑 配置方式

### 方式 1：配置文件

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id"
}
```

### 方式 2：环境变量

```bash
export SALESMARTLY_API_KEY="your_api_key"
export SALESMARTLY_PROJECT_ID="your_project_id"
```

## ⚠️ 注意事项

1. **API 域名**: `https://developer.salesmartly.com`
2. **Token 安全**: 不要泄露 API Key
3. **SSL 证书**: Python 请求时可能需要跳过证书验证
