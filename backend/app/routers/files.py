"""文件与生成相关接口：上传解析 / 在线输入 / HTML 生成（任务制+进度） / 摘要分类 / 图表洞察"""
import uuid, json, time, asyncio
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .. import config
from ..services import parser, generator, store, llm, ocr

router = APIRouter(prefix="/api", tags=["files"])

# ---- 生成任务进度存储（内存态，进程重启即清空，仅用于进行中的任务）----
_jobs: dict[str, dict] = {}
MAX_JOBS_KEEP = 60


def _job_update(job_id: str, **kw):
    job = _jobs.get(job_id)
    if job:
        job.update(kw)
        job["elapsed"] = round(time.time() - job["started"], 1)


async def _run_generate_job(job_id: str, fid: str, theme: str, model_id: str | None,
                            extra_req: str, cached: dict):
    """后台执行生成全流程，阶段化更新进度（前端轮询 /api/generate/progress/{job_id}）"""
    try:
        _job_update(job_id, stage="prepare", percent=4, message="校验数据与解析缓存…")
        from ..services import bigdata
        stats = bigdata.get_stats(fid)
        is_big = bool(stats)
        # 生成阶段占 10%~86%（LLM 生成耗时波动大，前端按时间平滑插值展示）
        _job_update(job_id, stage="design", percent=10,
                    message="AI 正在智能选型并设计页面（视觉框架 + 图表规划，约 2~4 分钟）…")
        if is_big:
            gen_task = asyncio.create_task(generator.generate_html_bigdata(
                cached["text"], cached["meta"], stats, theme, model_id, extra_req))
            summary_data = {}
        else:
            # 提速关键点：HTML 生成与摘要分类并行（原先串行，节省 30~60 秒）
            gen_task = asyncio.create_task(generator.generate_html(
                cached["text"], cached["meta"], theme, model_id, extra_req))
            sum_task = asyncio.create_task(generator.summarize(cached["text"][:6000], model_id))
        result = await gen_task
        _job_update(job_id, stage="render", percent=88, message="页面代码已生成，注入数据与导出组件…")
        if is_big:
            rec_id = uuid.uuid4().hex[:12]
            html_code = generator.inject_bigdata(gen["html_code"], rec_id, stats)
            html_code = generator.inject_export(html_code)
            html_path = config.GENERATED_DIR / f"{rec_id}.html"
            html_path.write_text(html_code, encoding="utf-8")
            result = {"id": rec_id, "html_code": html_code, "html_path": str(html_path)}
            summary_data = {}
        else:
            result["html_code"] = generator.inject_export(result["html_code"])
            config.GENERATED_DIR.joinpath(f"{result['id']}.html").write_text(result["html_code"], encoding="utf-8")
            try:
                summary_data = await sum_task
            except Exception:
                summary_data = {}
        _job_update(job_id, stage="save", percent=94, message="保存页面与写入历史记录…")
        rec = {
            "id": result["id"], "title": summary_data.get("title") or cached["meta"].get("file_name", "未命名"),
            "file_name": cached["meta"].get("file_name", ""), "source_type": cached["meta"].get("ext", "txt"),
            "summary": summary_data.get("summary", ""), "category": summary_data.get("category", "未分类"),
            "tags": json.dumps(summary_data.get("tags", []), ensure_ascii=False),
            "html_path": result["html_path"], "html_code": result["html_code"],
            "theme": theme, "model": model_id or "agnes-default", "file_id": fid,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        store.execute(
            "INSERT INTO records(id,title,file_name,source_type,summary,category,tags,html_path,html_code,theme,model,file_id,status,created_at) "
            "VALUES(:id,:title,:file_name,:source_type,:summary,:category,:tags,:html_path,:html_code,:theme,:model,:file_id,'active',:created_at)", rec)
        payload = {"id": rec["id"], "title": rec["title"], "summary": rec["summary"],
                   "category": rec["category"], "tags": summary_data.get("tags", []),
                   "suggested_theme": summary_data.get("suggested_theme", ""),
                   "html_code": result["html_code"], "preview_url": f"/api/preview/{result['id']}"}
        _job_update(job_id, stage="done", percent=100, status="done",
                    message="生成完成", result=payload)
    except llm.LLMError as e:
        _job_update(job_id, stage="error", percent=100, status="failed", message=str(e), error=str(e))
    except Exception as e:
        _job_update(job_id, stage="error", percent=100, status="failed",
                    message=f"生成失败: {e}", error=f"生成失败: {e}")
    finally:
        # 清理过早的历史任务，防止内存膨胀
        if len(_jobs) > MAX_JOBS_KEEP:
            done_ids = [k for k, v in _jobs.items() if v.get("status") in ("done", "failed")][:-20]
            for k in done_ids:
                _jobs.pop(k, None)

# 内存中缓存已解析原文（file_id -> {text, meta}），同时落盘 data/cache/{id}.json
CACHE_DIR = config.DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_put(fid, text, meta):
    (CACHE_DIR / f"{fid}.json").write_text(
        json.dumps({"text": text, "meta": meta}, ensure_ascii=False), encoding="utf-8")

def _cache_get(fid):
    f = CACHE_DIR / f"{fid}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """上传并解析文件，返回 file_id + 原文。zip 提取内部文档解析；不可解析类型给友好提示"""
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTS:
        if ext in (".exe", ".msi", ".dll", ".bat", ".apk", ".dmg", ".iso"):
            raise HTTPException(400, f"「{ext}」是程序/镜像文件，无法解析为文字内容。"
                                     f"请转换为 Word/PDF 等文档，或对关键内容截图后以图片上传（自动 OCR）")
        if ext in (".rar", ".7z"):
            raise HTTPException(400, f"暂不支持 {ext} 压缩包，请先解压或改用 zip 格式后重新上传")
        raise HTTPException(400, f"不支持的文件格式: {ext}（支持 docx/pptx/pdf/txt/md/csv/xlsx/json/html/图片/zip，≤{config.MAX_UPLOAD_MB}MB）")
    content = await file.read()
    if len(content) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"文件超过 {config.MAX_UPLOAD_MB}MB 限制")
    save_path = config.UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path.write_bytes(content)
    # 图片通道：走 OCR（支持长图切片有序合并、低清自动增强）
    if ext in ocr.IMAGE_EXTS:
        try:
            result = await ocr.ocr_image(str(save_path))
        except llm.LLMError as e:
            raise HTTPException(400, f"OCR 识别失败: {e}")
        except Exception as e:
            raise HTTPException(400, f"图片读取失败: {e}")
        fid = uuid.uuid4().hex[:12]
        _cache_put(fid, result["text"], result["meta"])
        return {"file_id": fid, "text": result["text"], "meta": result["meta"]}
    # 压缩包通道：提取内部可解析文档逐个解析后拼接
    if ext == ".zip":
        try:
            result = parser.parse_zip(str(save_path))
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(400, f"压缩包解析失败: {e}")
        fid = uuid.uuid4().hex[:12]
        _cache_put(fid, result["text"], result["meta"])
        return {"file_id": fid, "text": result["text"], "meta": result["meta"]}
    try:
        result = parser.parse_file(str(save_path))
    except Exception as e:
        raise HTTPException(400, f"解析失败: {e}")
    fid = uuid.uuid4().hex[:12]
    # 大文件检测：表格类且行数达标 -> 全量扫描聚合（明细落盘 NDJSON 供分页查询）
    if ext in (".xlsx", ".xls", ".csv"):
        from ..services import bigdata
        total_rows = _count_rows(save_path, ext)
        result["meta"]["total_rows"] = total_rows
        if total_rows >= bigdata.BIGDATA_THRESHOLD:
            try:
                stats = bigdata.scan_and_cache(fid, str(save_path))
                result["meta"].update(bigdata=True, total=stats["total"],
                                      stats_preview={"carriers": stats["carriers"], "sources": stats["sources"]})
            except Exception as e:
                raise HTTPException(400, f"大文件扫描失败: {e}")
    _cache_put(fid, result["text"], result["meta"])
    return {"file_id": fid, "text": result["text"], "meta": result["meta"]}

def _count_rows(path, ext) -> int:
    if ext == ".csv":
        with open(path, "rb") as f:
            return max(0, sum(1 for _ in f) - 1)
    from openpyxl import load_workbook
    wb = load_workbook(str(path), read_only=True)
    n = wb.worksheets[0].max_row - 1
    wb.close()
    return max(0, n)

@router.post("/parse-text")
async def parse_text(text: str = Form(...), title: str = Form("")):
    """在线粘贴文本输入"""
    if not text.strip():
        raise HTTPException(400, "文本内容为空")
    fid = uuid.uuid4().hex[:12]
    meta = {"file_name": title or "在线输入文本", "ext": "txt", "char_count": len(text)}
    _cache_put(fid, text, meta)
    return {"file_id": fid, "text": text, "meta": meta}

@router.get("/cache/{fid}")
async def get_cache(fid: str):
    data = _cache_get(fid)
    if not data:
        raise HTTPException(404, "解析缓存不存在或已过期")
    return data

@router.post("/generate")
async def generate(payload: dict):
    """创建生成任务（立即返回 job_id，前端轮询 /api/generate/progress/{job_id} 获取真实进度）"""
    fid = payload.get("file_id")
    theme = payload.get("theme", "auto")
    model_id = payload.get("model_id")
    extra_req = payload.get("extra_req", "")
    cached = _cache_get(fid)
    if not cached:
        raise HTTPException(404, "file_id 无效，请先上传文件或输入文本")
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"stage": "queued", "percent": 0, "message": "任务排队中…",
                     "status": "running", "error": None, "result": None,
                     "started": time.time(), "elapsed": 0}
    asyncio.create_task(_run_generate_job(job_id, fid, theme, model_id, extra_req, cached))
    return {"job_id": job_id}


@router.get("/generate/progress/{job_id}")
async def generate_progress(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在或已过期")
    # elapsed 必须在轮询时实时计算：任务执行中途（如 LLM 生成阶段）没有阶段切换，
    # 若读存储值会一直停留在上一阶段切换时的旧值，导致前端进度卡死、计时归零
    return {"stage": job["stage"], "percent": job["percent"], "message": job["message"],
            "status": job["status"], "error": job["error"], "result": job["result"],
            "elapsed": round(time.time() - job["started"], 1)}

@router.post("/summarize")
async def summarize(payload: dict):
    cached = _cache_get(payload.get("file_id", ""))
    if not cached:
        raise HTTPException(404, "file_id 无效")
    try:
        return await generator.summarize(cached["text"], payload.get("model_id"))
    except llm.LLMError as e:
        raise HTTPException(502, str(e))

@router.post("/insight")
async def insight(payload: dict):
    cached = _cache_get(payload.get("file_id", ""))
    if not cached:
        raise HTTPException(404, "file_id 无效")
    try:
        return await generator.insight(cached["text"], payload.get("model_id"))
    except llm.LLMError as e:
        raise HTTPException(502, str(e))

@router.post("/solve")
async def solve(payload: dict):
    """题目解答：识别文档中的题目并逐题给出步骤与答案"""
    cached = _cache_get(payload.get("file_id", ""))
    if not cached:
        raise HTTPException(404, "file_id 无效")
    try:
        return await generator.solve(cached["text"], payload.get("model_id"))
    except llm.LLMError as e:
        raise HTTPException(502, str(e))

@router.post("/convert")
async def convert(file: UploadFile = File(...), target: str = Form(...)):
    """格式转换：docx/pptx/pdf/txt/md/csv/xlsx -> txt/docx/pdf/xlsx/csv，返回转换后的文件流"""
    from fastapi.responses import FileResponse
    from ..services import convert as svc
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTS:
        raise HTTPException(400, f"不支持的文件格式: {ext}")
    save_path = config.UPLOAD_DIR / f"convert_{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path.write_bytes(await file.read())
    try:
        result = await svc.convert(str(save_path), target)
    except Exception as e:
        raise HTTPException(400, f"转换失败: {e}")
    return FileResponse(result["path"], filename=result["file_name"])

@router.get("/preview/{rec_id}")
async def preview(rec_id: str):
    """本地预览生成的 HTML（iframe src 直接指向此接口；旧记录动态补注入导出组件）"""
    rows = store.query("SELECT html_code FROM records WHERE id=?", (rec_id,))
    if not rows:
        raise HTTPException(404, "记录不存在")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(generator.inject_export(rows[0]["html_code"]))
