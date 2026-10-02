"""LLM 接入层：默认 Agnes（OpenAI 兼容），支持用户自定义模型（base_url + api_key）"""
import asyncio
import httpx
from .. import config
from . import store

class LLMError(Exception):
    pass

# 瞬态网络错误（代理断流/超时/连接重置），可安全重试
_TRANSIENT = (httpx.ReadError, httpx.WriteError, httpx.ConnectError,
              httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout,
              httpx.RemoteProtocolError)

def _resolve(model_id: str | None):
    """按 model_id 解析出 (base_url, api_key, model_name)"""
    if not model_id or model_id in ("agnes-default", "agnes"):
        return config.AGNES_BASE_URL, config.AGNES_API_KEY, config.AGNES_DEFAULT_MODEL
    rows = store.query("SELECT * FROM models WHERE id=?", (model_id,))
    if not rows:
        raise LLMError(f"模型不存在: {model_id}")
    m = rows[0]
    return m["base_url"], m["api_key"], m["name"]

async def chat(messages: list, model_id: str | None = None, temperature: float = 0.7,
               max_tokens: int = 8000, timeout: float = 300) -> str:
    base_url, api_key, model = _resolve(model_id)
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = base_url.rstrip("/") + "/chat/completions"
    # trust_env=False：忽略系统/环境变量代理，直连模型服务（本机代理挂掉会截断长响应导致 ReadError）
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise LLMError(f"模型调用失败 HTTP {resp.status_code}: {resp.text[:300]}")
                data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise LLMError(f"模型响应格式异常: {str(data)[:300]}")
        except _TRANSIENT as e:          # 瞬态网络错误：退避后重试
            last_err = e
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
        except LLMError:
            raise                        # 业务错误（配额/鉴权/格式）不重试
    raise LLMError(f"模型网络连接失败（已重试 3 次）: {last_err}")

async def list_remote_models(base_url: str, api_key: str) -> list:
    """拉取自定义服务端的可用模型列表"""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        resp = await client.get(base_url.rstrip("/") + "/models", headers=headers)
        if resp.status_code != 200:
            raise LLMError(f"获取模型列表失败 HTTP {resp.status_code}")
        data = resp.json()
    return [m.get("id") for m in data.get("data", [])]

def extract_html(text: str) -> str:
    """从 LLM 输出中提取完整 HTML 代码"""
    t = text.strip()
    if "```" in t:
        # 优先取 ```html 代码块
        import re
        blocks = re.findall(r"```(?:html)?\s*\n?([\s\S]*?)```", t)
        for b in blocks:
            if "<html" in b.lower() or "<!doctype" in b.lower():
                return b.strip()
        if blocks and "<body" in blocks[0].lower():
            return blocks[0].strip()
    if "<html" in t.lower() or "<!doctype" in t.lower():
        return t
    raise LLMError("模型未返回有效的 HTML 内容")
