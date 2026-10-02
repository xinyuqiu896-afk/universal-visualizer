"""记录管理接口：历史 / 收藏 / 回收站 / 导出下载 / 公开分享"""
import uuid, json, re
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from .. import config
from ..services import store

router = APIRouter(prefix="/api", tags=["records"])

def _row_brief(r):
    return {"id": r["id"], "title": r["title"], "file_name": r["file_name"], "source_type": r["source_type"],
            "summary": r["summary"], "category": r["category"], "tags": json.loads(r["tags"] or "[]"),
            "theme": r["theme"], "model": r["model"], "favorite": bool(r["favorite"]),
            "status": r["status"], "share_id": r["share_id"], "created_at": r["created_at"]}

@router.get("/history")
async def history(favorite: int = 0, category: str = "", keyword: str = ""):
    sql, params = "SELECT * FROM records WHERE status='active'", []
    if favorite:
        sql += " AND favorite=1"
    if category:
        sql += " AND category LIKE ?"
        params.append(f"%{category}%")
    if keyword:
        sql += " AND (title LIKE ? OR summary LIKE ? OR file_name LIKE ?)"
        params += [f"%{keyword}%"] * 3
    sql += " ORDER BY created_at DESC"
    return [_row_brief(r) for r in store.query(sql, params)]

@router.get("/trash")
async def trash():
    return [_row_brief(r) for r in store.query("SELECT * FROM records WHERE status='trashed' ORDER BY created_at DESC")]

@router.post("/records/{rec_id}/favorite")
async def toggle_favorite(rec_id: str):
    store.execute("UPDATE records SET favorite = 1 - favorite WHERE id=?", (rec_id,))
    return {"ok": True}

@router.delete("/records/{rec_id}")
async def to_trash(rec_id: str):
    """软删除 -> 回收站"""
    store.execute("UPDATE records SET status='trashed' WHERE id=?", (rec_id,))
    return {"ok": True}

@router.post("/records/{rec_id}/restore")
async def restore(rec_id: str):
    store.execute("UPDATE records SET status='active' WHERE id=?", (rec_id,))
    return {"ok": True}

@router.delete("/records/{rec_id}/purge")
async def purge(rec_id: str):
    """彻底删除（回收站）"""
    rows = store.query("SELECT html_path FROM records WHERE id=?", (rec_id,))
    if rows and rows[0]["html_path"]:
        Path(rows[0]["html_path"]).unlink(missing_ok=True)
    store.execute("DELETE FROM records WHERE id=?", (rec_id,))
    return {"ok": True}

@router.get("/records/{rec_id}/data")
async def record_data(rec_id: str, page: int = 1, size: int = 100,
                      carrier: str = "", source: str = "", keyword: str = ""):
    """大文件明细分页查询（17 万+ 条全部可查，支持运营商/来源/关键词过滤）"""
    rows = store.query("SELECT file_id FROM records WHERE id=?", (rec_id,))
    if not rows or not rows[0]["file_id"]:
        raise HTTPException(404, "该记录无关联数据文件")
    from ..services import bigdata
    try:
        return bigdata.load_page(rows[0]["file_id"], page, size, carrier, source, keyword)
    except FileNotFoundError:
        raise HTTPException(404, "明细数据文件不存在")

@router.post("/records/{rec_id}/share")
async def share(rec_id: str):
    """生成公开访问链接（/share/{share_id} 任何人可访问）"""
    rows = store.query("SELECT share_id FROM records WHERE id=?", (rec_id,))
    if not rows:
        raise HTTPException(404, "记录不存在")
    sid = rows[0]["share_id"] or uuid.uuid4().hex[:10]
    store.execute("UPDATE records SET share_id=? WHERE id=?", (sid, rec_id))
    return {"share_id": sid, "share_url": f"/share/{sid}"}

@router.get("/records/{rec_id}/export")
async def export(rec_id: str):
    rows = store.query("SELECT html_code, title FROM records WHERE id=?", (rec_id,))
    if not rows:
        raise HTTPException(404, "记录不存在")
    safe = re.sub(r'[\\/:*?"<>|]', "_", rows[0]["title"] or rec_id)
    out = config.EXPORT_DIR / f"{safe}.html"
    from ..services import generator
    out.write_text(generator.inject_export(rows[0]["html_code"]), encoding="utf-8")
    return FileResponse(str(out), filename=out.name, media_type="text/html")

# ---- 公开分享路由（无需鉴权）----
share_router = APIRouter(tags=["share"])

@share_router.get("/share/{share_id}", response_class=HTMLResponse)
async def public_share(share_id: str):
    rows = store.query("SELECT html_code FROM records WHERE share_id=? AND status='active'", (share_id,))
    if not rows:
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:40px'>链接无效或内容已删除</h2>", status_code=404)
    from ..services import generator
    return HTMLResponse(generator.inject_export(rows[0]["html_code"]))
