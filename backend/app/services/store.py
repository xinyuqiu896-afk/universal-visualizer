"""SQLite 数据层：历史记录 / 收藏 / 回收站 / 分享 / 自定义模型 / 系统设置"""
import sqlite3, json, threading
from .. import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    source_type TEXT,
    summary TEXT,
    category TEXT,
    tags TEXT,               -- JSON 数组
    html_path TEXT,
    html_code TEXT,
    theme TEXT,
    model TEXT,
    file_id TEXT,            -- 关联解析缓存/大文件明细
    favorite INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',   -- active / trashed
    share_id TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT,
    base_url TEXT,
    api_key TEXT,
    is_default INTEGER DEFAULT 0,
    builtin INTEGER DEFAULT 0,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = get_conn()
        conn.executescript(SCHEMA)
        # 旧库兼容：补 file_id 列
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(records)")]
        if "file_id" not in cols:
            conn.execute("ALTER TABLE records ADD COLUMN file_id TEXT")
        # 内置 Agnes 默认模型（幂等）
        conn.execute(
            "INSERT OR IGNORE INTO models(id,name,base_url,api_key,is_default,builtin,created_at) VALUES(?,?,?,?,1,1,datetime('now','localtime'))",
            ("agnes-default", "Agnes 大模型（内置默认）", config.AGNES_BASE_URL, config.AGNES_API_KEY),
        )
        conn.commit()
        conn.close()

def query(sql, params=()):
    with _lock:
        conn = get_conn()
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows

def execute(sql, params=()):
    with _lock:
        conn = get_conn()
        cur = conn.execute(sql, params)
        conn.commit()
        n = cur.rowcount
        conn.close()
        return n

# ---------- settings ----------
def get_setting(key, default=None):
    rows = query("SELECT value FROM settings WHERE key=?", (key,))
    return json.loads(rows[0]["value"]) if rows else default

def set_setting(key, value):
    execute(
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value, ensure_ascii=False)),
    )
