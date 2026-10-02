# 万能可视化工具（Universal Visualizer）

解析用户上传的 Word / PPT / PDF / TXT / Markdown / CSV / Excel / JSON / HTML / **图片（OCR）** 等文件，调用 **Agnes 大模型**完成内容总结与分类，智能选型视觉主题并生成高质感可视化 HTML 页面 —— 中间栏看原文，右侧大区域在线预览、缩放、本地预览、**导出 PDF** 与公开分享；生成全程有**真实进度条**。

## ✨ 核心特性

- **图片 OCR**：上传图片自动 OCR 识别（Agnes 视觉模型）；**长图**（高宽比≥2.2 或高>2600px）自动切片有序合并，重叠区按行去重不漏字不重复；**低清图**（宽<720px）自动放大+锐化增强后识别；偶发视觉失效自动重试
- **真实生成进度**：任务制生成（job_id）+ 轮询接口，前端环形进度 + 阶段文案 + 已用时/预计剩余；普通模式「HTML 生成与摘要分类并行」提速 30~60 秒
- **PDF 导出**：每张生成页右下角有「导出 PDF」悬浮按钮（含打印样式：保留配色、卡片不跨页截断）；工具栏也有「导出 PDF」一键调起，版式与页面显示完全一致
- **生成页动效**：入场阶梯淡入、滚动显现（IntersectionObserver）、数字 count-up、卡片 hover 过渡、ECharts 动画，尊重 prefers-reduced-motion
- **大文件模式**：≥1000 行表格自动全量扫描聚合（如 17.8 万条通讯录），LLM 只出页面框架，数据运行时注入 + 明细分页 API 全量可查

## 一、技术栈与选型理由

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | **Python + FastAPI** | 文档解析生态无可替代：python-docx / python-pptx / pdfplumber / openpyxl 全是成熟库；原生 async 适合等待 LLM 长响应；自动生成 /docs 接口文档 |
| 前端 | **Vue3 + Element Plus + Vite** | Upload/Layout/Dialog/Progress 组件开箱即用；中文文档与团队上手成本最低 |
| 图表 | **ECharts 5**（页面内 CDN + 洞察面板本地引入） | 大模型生成的 HTML 内嵌 ECharts 即可渲染数据图表 |
| 存储 | **SQLite**（零部署） | 历史记录/收藏/回收站/模型配置单文件即用，后续可平滑迁移 MySQL |
| 模型 | **Agnes AI**（OpenAI 兼容协议）+ 自定义模型接入 | Base URL `https://apihub.agnes-ai.com/v1`，更换模型只改 base_url/api_key/模型名 |

> **模型档位说明（重要）**：免费密钥仅可用 **flash 系列**（`agnes-2.5-flash` / `agnes-3.0-flash`，均带深度推理）；`agnes-2.5-pro` 等为付费档，调用会报 `insufficient_user_quota`。默认已配置 `agnes-2.5-flash`。JSON 类输出（摘要/洞察）内置「解析失败自动降温重试」机制，规避 reasoning 模型偶发的非法 JSON。

> Java/Spring Boot 未选：文档解析需依赖 Apache POI 等重量级方案且 PDF 表格提取弱；React 与 Element Plus 组合成熟度不如 Vue3 生态。Python 在"文件理解 + AI 调用"场景是确定性最优解。

## 二、目录结构

```
万能可视化/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口（CORS / 路由注册 / 静态挂载）
│   │   ├── config.py               # Agnes 接入参数 / 上传限制 / 路径
│   │   ├── services/
│   │   │   ├── parser.py           # 多格式真实解析引擎
│   │   │   ├── llm.py              # LLM 统一接入层（Agnes + 自定义）
│   │   │   ├── generator.py        # HTML 智能选型生成 / 摘要分类 / 图表洞察
│   │   │   ├── convert.py          # 格式转换引擎
│   │   │   └── store.py            # SQLite 数据层（建表幂等）
│   │   └── routers/
│   │       ├── files.py            # 上传/在线输入/生成/摘要/洞察/转换/预览
│   │       ├── records.py          # 历史/收藏/回收站/导出/公开分享
│   │       ├── models_router.py    # 模型接入管理
│   │       └── settings.py         # 系统设置 / 内置案例
│   ├── requirements.txt
│   └── (运行时生成 data/ uploads/ generated/ exports/)
└── frontend/
    ├── src/
    │   ├── App.vue                 # 三栏布局（左功能栏/中原文/右预览）+ 全局状态
    │   ├── api.js                  # 全部接口封装
    │   ├── styles.css
    │   └── components/
    │       └── modules/            # 13 个功能面板
    │           ├── UploadPanel.vue      文件上传与在线输入
    │           ├── BatchPanel.vue       批量处理
    │           ├── ConvertPanel.vue     格式转换
    │           ├── TemplatePanel.vue    模板与主题中心（7 套主题）
    │           ├── SummaryPanel.vue     摘要与标签分类
    │           ├── InsightPanel.vue     图表洞察（ECharts 渲染）
    │           ├── HistoryPanel.vue     历史记录
    │           ├── FavPanel.vue         收藏
    │           ├── TrashPanel.vue       回收站（软删除/恢复/彻底删除）
    │           ├── ExportPanel.vue      导出与分享
    │           ├── ModelPanel.vue       Agent 模型接入（内置 Agnes + 自定义）
    │           ├── CasesPanel.vue       案例查看（3 个内置案例）
    │           └── SettingsPanel.vue    系统设置
    └── package.json
```

## 三、启动说明

### 1. 后端（端口 8000）

```bash
cd backend
# 建议使用独立虚拟环境
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- 接口文档（Swagger）：http://localhost:8000/docs
- 首次启动自动建库
- **模型密钥**：复制 `backend/.env.example` 为 `backend/.env`，填入你的 Agnes API Key（[免费注册](https://apihub.agnes-ai.com)），或直接设置环境变量 `AGNES_API_KEY`。密钥不会入库，请勿提交到公开仓库

### 2. 前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 ，Vite 已配置代理，`/api`、`/share` 请求自动转发到 8000 后端。

### 3. 快速体验

1. 左侧「案例查看」→ 载入「季度经营分析报告」
2. 「模板与主题中心」选「智能选型」
3. 中间原文栏顶部点「生成可视化」（或左侧上传自己的文件）
4. 右侧查看结果：`-/+` 缩放、「公开链接」生成 `/share/{id}` 可分享给任何人

## 四、接口设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/upload` | 上传并解析文件 → `{file_id, text, meta}` |
| POST | `/api/parse-text` | 在线文本输入 → `{file_id, text, meta}` |
| POST | `/api/generate` | **核心**：`{file_id, theme, model_id, extra_req}` → 生成 HTML + 自动摘要分类，写入历史 |
| POST | `/api/summarize` | 摘要/分类/标签/建议主题（JSON） |
| POST | `/api/insight` | 图表洞察：提取数据 → ECharts option + 洞察结论 |
| POST | `/api/convert` | 格式转换（multipart），返回文件流 |
| GET | `/api/preview/{id}` | 生成的 HTML 预览（iframe 直接指向） |
| GET | `/api/history` / `/api/trash` | 历史列表（支持收藏/分类/关键词过滤）/ 回收站 |
| POST/DELETE | `/api/records/{id}/favorite` `·/restore` `·/purge` | 收藏切换 / 回收站恢复 / 彻底删除 |
| POST | `/api/records/{id}/share` | 生成公开链接 → `GET /share/{share_id}`（无需鉴权，任何人可访问） |
| GET | `/api/records/{id}/export` | 导出 HTML 文件下载 |
| GET/POST/DELETE | `/api/models*` | 模型接入管理：列表/添加/删除/设默认/连通测试 |
| GET/POST | `/api/settings` | 系统设置（默认主题/温度/上下文长度） |
| GET | `/api/cases` | 内置案例 |

## 五、实现要点

- **真实解析**：docx 提取段落+表格（含标题层级）、pptx 逐页文本+表格+备注、pdf 逐页文本+表格、xlsx/csv 逐行读取，全部落成结构化文本。
- **大文件模式（海量明细数据，≥1000 行自动启用）**：上传时对 xlsx/csv 全量流式扫描 —— 聚合统计（总条数/运营商/数据来源/号段分布）落盘 `data/bigdata/{fid}.stats.json`，明细落盘 NDJSON（17.8 万条约 20MB）。LLM 只负责生成页面框架与文案（大文件专用 prompt：`BIGDATA_GEN_SYSTEM`），所有数字从注入的 `window.PAGE_DATA` 读取，明细表运行时调用 `GET /api/records/{id}/data?page&size&carrier&source&keyword` 分页查询 —— **架构上杜绝 LLM 手写 17 万条数据导致的缺失/编造**。
- **智能选型**：生成 prompt 要求模型分析内容主题后自动匹配 7 套视觉风格之一（科技蓝/商务黑金/清新绿/暖橙/极简/暗黑霓虹），并输出完整单文件 HTML（内联 CSS + ECharts CDN），后端用正则提取代码块并落盘。
- **防 token 溢出**：原文按 `MAX_CONTEXT_CHARS`（默认 14000 字）截断后送模型。
- **软删除机制**：删除先进回收站（status='trashed'），可恢复或彻底删除（同时清理生成文件）。
- **公开分享**：`/share/{share_id}` 为独立无鉴权路由，任何拿到链接的浏览器都能访问。

## 六、开源许可与作者

- License: **MIT**
- 作者：**QXY**（QQ：1181426980）
