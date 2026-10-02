"""万能可视化工具 - FastAPI 后端入口
启动: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .services import store
from .routers import files, records, models_router, settings

app = FastAPI(title="万能可视化工具 API", version="1.0.0",
              description="解析 Word/PPT/PDF/TXT 等文件，AI 总结分类并生成高质感可视化 HTML")

# CORS：允许 Vite 开发服务器跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_methods=["*"], allow_headers=["*"],
)

store.init_db()
app.include_router(files.router)
app.include_router(records.router)
app.include_router(records.share_router)
app.include_router(models_router.router)
app.include_router(settings.router)

# 生成的 HTML 静态目录（备用直链）
from . import config
app.mount("/generated", StaticFiles(directory=str(config.GENERATED_DIR)), name="generated")
app.mount("/exports", StaticFiles(directory=str(config.EXPORT_DIR)), name="exports")

@app.get("/")
async def root():
    return {"app": "万能可视化工具", "docs": "/docs", "share_example": "/share/{share_id}"}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(config.BASE_DIR / "favicon.ico")) if (config.BASE_DIR / "favicon.ico").exists() else {"ok": 1}
