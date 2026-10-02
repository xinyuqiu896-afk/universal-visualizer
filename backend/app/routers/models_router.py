"""模型接入管理：内置 Agnes + 用户自定义模型（OpenAI 兼容协议）"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from .. import config
from ..services import store, llm

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("")
async def list_models():
    rows = store.query("SELECT * FROM models ORDER BY builtin DESC, created_at DESC")
    return [{"id": r["id"], "name": r["name"], "base_url": r["base_url"],
             "api_key": (r["api_key"][:8] + "****") if r["api_key"] else "",
             "api_key_full": r["api_key"], "is_default": bool(r["is_default"]), "builtin": bool(r["builtin"])} for r in rows]

@router.post("")
async def add_model(payload: dict):
    name, base_url, api_key = payload.get("name", "").strip(), payload.get("base_url", "").strip(), payload.get("api_key", "").strip()
    if not (name and base_url and api_key):
        raise HTTPException(400, "name / base_url / api_key 均必填")
    mid = "m-" + uuid.uuid4().hex[:8]
    store.execute("INSERT INTO models(id,name,base_url,api_key,is_default,builtin,created_at) VALUES(?,?,?,?,0,0,?)",
                  (mid, name, base_url.rstrip("/"), api_key, datetime.now().isoformat(timespec="seconds")))
    return {"id": mid, "ok": True}

@router.delete("/{model_id}")
async def del_model(model_id: str):
    row = store.query("SELECT builtin FROM models WHERE id=?", (model_id,))
    if not row:
        raise HTTPException(404, "模型不存在")
    if row[0]["builtin"]:
        raise HTTPException(400, "内置模型不可删除")
    store.execute("DELETE FROM models WHERE id=?", (model_id,))
    return {"ok": True}

@router.post("/{model_id}/default")
async def set_default(model_id: str):
    store.execute("UPDATE models SET is_default=0")
    store.execute("UPDATE models SET is_default=1 WHERE id=?", (model_id,))
    return {"ok": True}

@router.post("/probe")
async def probe(payload: dict):
    """连通性测试：尝试拉取远端模型列表"""
    try:
        models = await llm.list_remote_models(payload["base_url"].rstrip("/"), payload["api_key"])
        return {"ok": True, "remote_models": models[:50]}
    except Exception as e:
        raise HTTPException(502, f"连接失败: {e}")

@router.get("/builtin-info")
async def builtin_info():
    return {"provider": "Agnes AI", "base_url": config.AGNES_BASE_URL,
            "default_model": config.AGNES_DEFAULT_MODEL, "fast_model": config.AGNES_FAST_MODEL,
            "docs": "https://agnes-ai.com/zh-Hans/docs/overview"}
