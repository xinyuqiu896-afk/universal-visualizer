"""全局配置：路径、默认模型、Agnes 接入参数"""
import os
from pathlib import Path

# ---- 轻量 .env 加载（无第三方依赖；仅填充未设置的环境变量）----
def _load_dotenv():
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))

_load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated"
EXPORT_DIR = BASE_DIR / "exports"
for d in (DATA_DIR, UPLOAD_DIR, GENERATED_DIR, EXPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "app.db"

# ---- Agnes 大模型（默认接入，OpenAI 兼容协议）----
AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"
# 密钥从环境变量 AGNES_API_KEY 或 backend/.env 读取，绝不硬编码入库
AGNES_API_KEY = os.environ.get("AGNES_API_KEY", "")
# 免费密钥可用档位：flash 系列（pro 为付费档，会报 insufficient_user_quota）
AGNES_DEFAULT_MODEL = "agnes-2.5-flash"    # 默认：免费可用，带深度推理，生成质量好
AGNES_FAST_MODEL = "agnes-3.0-flash"       # 快速：免费可用，批量处理/简单任务

# 文本送入 LLM 的最大长度（超出截断，防止 token 溢出）
MAX_CONTEXT_CHARS = 14000

# 上传白名单（图片走 OCR 通道，zip 走压缩包通道）
ALLOWED_EXTS = {".docx", ".doc", ".pptx", ".pdf", ".txt", ".md", ".csv", ".xlsx", ".xls", ".json", ".html",
                ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".zip"}
MAX_UPLOAD_MB = 30
