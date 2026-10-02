"""HTML 可视化页面生成器：LLM 根据内容主题智能选型配色/版式，输出单文件高质感 HTML"""
import json, uuid
from datetime import datetime
from .. import config
from . import llm
from . import store

THEMES = {
    "auto":       "根据内容主题自行判断并选择最贴合的视觉风格（智能选型）",
    "tech-blue":  "科技蓝：深海军蓝底 #0B1220 + 电光蓝 #3B82F6 点缀，玻璃拟态卡片，适合科技/互联网/数据类内容",
    "biz-gold":   "商务黑金：炭黑 #111 底 + 香槟金 #C9A227 点缀，衬线标题，适合金融/商业/战略报告",
    "fresh-green":"清新自然：米白 #F7F5EF 底 + 森林绿 #2F6B4F，适合环保/农业/健康类内容",
    "warm-orange":"暖橙活力：奶油白 #FFF8F0 底 + 珊瑚橙 #E8622C，适合教育/生活/营销类内容",
    "minimal":    "极简杂志：纯白底 + 近黑文字 + 一处强调色，大量留白，编辑排版风",
    "dark-neon":  "暗黑霓虹：#0A0A12 底 + 霓虹紫/青渐变，适合游戏/创意/潮流内容",
}

GEN_SYSTEM = f"""你是「万能可视化工具」的资深前端视觉设计师兼数据可视化工程师。
任务：把用户提供的文档内容转化为一个**单文件、可直接在浏览器打开的高质量 HTML 展示页**。

## 视觉要求（重要）
1. 【智能选型】{THEMES['auto']}。若用户指定了主题，则严格按指定主题执行。
2. 产出必须具备一线大厂产品页面的高级质感：
   - 设计系统：用 CSS 变量定义 --bg/--surface/--primary/--accent/--text/--text-sub/--radius/--shadow 全局令牌；
   - 字体层级：Hero 大标题 clamp(34px,5vw,56px) 加字重与字距，节标题 22-28px，正文 15-16px/1.9 行高，
     数字一律 font-variant-numeric: tabular-nums；
   - 质感细节：卡片细边框 + 多层柔和阴影、渐变强调（主色→辅助色 135deg）、微妙玻璃拟态
     （backdrop-filter: blur 用于导航/悬浮元素）、1px 高光描边（rgba(255,255,255,.08)）。
3. 页面结构：顶部 Hero 区（大标题+一句话摘要+元信息徽章）→ 核心内容区（分节卡片/时间线/对比栏等，
   依据内容形态选择最合适的版式）→ 数据可视化区 → 尾注。区块之间用 section 编号或装饰线增强节奏感。
4. 【动效与过渡（必须实现，直接影响成品评级）】
   a. 入场动画：页面加载时 Hero 元素依次淡入上移（CSS animation + animation-delay 阶梯延迟 0.08s/项）；
   b. 滚动显现：用 IntersectionObserver 给每个 section/卡片加 .reveal 类，进入视口时
      opacity 0→1 + translateY(24px)→0 过渡 0.6s cubic-bezier(.22,.61,.36,1)，加 transition-delay 制造级联；
   c. 数字滚动：关键指标数字用 rAF 实现 count-up（1.2s ease-out，支持千分位与小数）；
   d. Hover 交互：卡片 hover 上浮 translateY(-4px) + 阴影加深 + 边框亮起，过渡 .25s；
   e. 图表动画：ECharts 开启动画（animationDuration 900 + animationEasing 'cubicOut'），
      饼图用 expansion，加载时容器有淡入；
   f. 尊重 prefers-reduced-motion：有该媒体查询时关闭动画。
5. 图表：引入 ECharts CDN（https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js），
   按内容真实数据构造 option，图表配色与页面主题一致；无数据则不放图表，禁止编造精确数据
   （可基于文中描述做示意性可视化时，需标注"示意图"）。
6. 所有 CSS 内联在 <style> 中；禁止外部 CSS 文件；禁止占位假文（lorem ipsum）。
7. 中文内容用系统中文字体栈：'PingFang SC','Microsoft YaHei',sans-serif；标题可用衬线增强质感。
8. 响应式：max-width 1100px 居中，移动端不破版。
9. 【打印/PDF（必须包含）】样式末尾写 @media print {{
      .no-print, [data-no-print] {{ display:none !important; }}
      * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      section, .card {{ page-break-inside: avoid; break-inside: avoid; }}
      body {{ background: var(--bg) !important; }}
   }}
10. 【JS 语法自检】<script> 内必须使用标准 JS 语法：HTML 标签的 style 属性只能写 CSS（font-weight，不是 fontWeight）；
   ECharts option 遵循官方写法，字符串引号配对完整，输出前逐段自检避免语法错误导致图表不渲染。

## 输出要求
- 只输出完整 HTML 代码（从 <!DOCTYPE html> 到 </html>），不要任何解释文字，不要 markdown 代码块围栏。
- 内容必须来自用户文档的真实信息，信息密度要高：把文档里的要点、数据、结构都提炼呈现出来。"""

SUMMARY_SYSTEM = """你是文档分析专家。分析用户提供的文档内容，输出严格的 JSON（不要 markdown 围栏、不要解释）：
{"title": "提炼的文档标题", "summary": "150-250字内容总结",
"key_points": ["从原文提炼的关键句1（尽量保留原文表述，30-60字）", "关键句2", "关键句3", "关键句4", "关键句5"],
"category": "分类（从这些里选或自拟：商业报告/技术文档/教育材料/会议纪要/营销策划/学术研究/法律文书/新闻资讯/其他）",
"tags": ["标签1","标签2","标签3","标签4","标签5"], "keywords": ["关键词1","关键词2"],
"content_type": "内容形态：报告类/叙述类/数据类/教程类/演讲类", "suggested_theme": "建议主题：tech-blue/biz-gold/fresh-green/warm-orange/minimal/dark-neon 之一"}
要求：key_points 为 3-5 条核心关键句，按原文出现顺序排列，每条必须是原文中存在或贴近原文的表述（便于在原文中定位），不要笼统概括。"""

INSIGHT_SYSTEM = """你是数据分析专家。从用户提供的文档内容中提取可量化信息，构造图表洞察。输出严格 JSON（不要围栏）：{"charts": [{"title": "图表标题", "type": "bar|line|pie|radar", "note": "数据来源说明（来自文档哪部分/是否示意）",
"option": {ECharts option 对象，含 xAxis/series 等，配色用一组和谐色}}], "insights": ["洞察结论1", "洞察结论2"]}
要求：
1. 1-4 个图表；若文档无可量化数据，构造 1 个基于内容权重的示意雷达/条形图并在 note 标注"示意"；insights 给 2-4 条一针见血的结论。
2. 【严格纯 JSON】option 内禁止任何 JavaScript 函数/箭头函数/表达式（如 formatter 不能写 value=>...，改用字符串模板 "{value}%" 或 "{c}"）；禁止注释；禁止尾逗号；所有 key 用双引号。"""

SOLVE_SYSTEM = """你是资深解题专家。分析用户提供的文档，识别其中的题目（历年真题、计算题、应用题、选择题、证明题等）并逐题解答。输出严格 JSON（不要 markdown 围栏、不要解释）：
{"title": "文档题目集标题", "is_question_doc": true, "items": [
{"question": "题目原文（精简保留关键条件与数据）", "type": "计算题|选择题|证明题|应用题|简答题",
"steps": ["解题步骤1（含公式与代入过程）", "步骤2"], "answer": "最终答案（加粗关键数值）"}]}
要求：
1. 最多解答 8 题超出的在 title 注明；按文档中题目顺序排列，步骤 2-5 步清晰可复现，计算必须验算准确。
2. 若文档不含题目，输出 {"title": "文档标题", "is_question_doc": false, "items": []}。
3. 【严格纯 JSON】禁止注释、尾逗号，所有 key 用双引号。"""

async def generate_html(doc_text: str, meta: dict, theme: str = "auto",
                        model_id: str | None = None, extra_req: str = "") -> dict:
    """调用 LLM 生成 HTML，落盘并返回 {record} 数据"""
    theme_desc = THEMES.get(theme, THEMES["auto"])
    user_prompt = f"""【文档元信息】文件：{meta.get('file_name','在线输入')} | 格式：{meta.get('ext','txt')} | 字数：{meta.get('char_count', len(doc_text))}
【指定主题】{theme if theme != 'auto' else 'auto（你来自智能选型，并在页面注释里说明你为什么选这个风格）'}
【附加要求】{extra_req or '无'}

【文档内容】
{doc_text[:config.MAX_CONTEXT_CHARS]}"""
    raw = await llm.chat(
        [{"role": "system", "content": GEN_SYSTEM + f"\n当前指定主题说明：{theme_desc}"},
         {"role": "user", "content": user_prompt}],
        model_id=model_id, temperature=0.65, max_tokens=16000)
    html_code = llm.extract_html(raw)

    rec_id = uuid.uuid4().hex[:12]
    html_path = config.GENERATED_DIR / f"{rec_id}.html"
    html_path.write_text(html_code, encoding="utf-8")
    return {"id": rec_id, "html_code": html_code, "html_path": str(html_path)}

async def summarize(doc_text: str, model_id: str | None = None) -> dict:
    return await _chat_json(SUMMARY_SYSTEM, doc_text[:config.MAX_CONTEXT_CHARS], model_id,
                            max_tokens=1200, temperature=0.3)

async def insight(doc_text: str, model_id: str | None = None) -> dict:
    return await _chat_json(INSIGHT_SYSTEM, doc_text[:config.MAX_CONTEXT_CHARS], model_id,
                            max_tokens=4000, temperature=0.4)

async def solve(doc_text: str, model_id: str | None = None) -> dict:
    return await _chat_json(SOLVE_SYSTEM, doc_text[:config.MAX_CONTEXT_CHARS], model_id,
                            max_tokens=6000, temperature=0.25)

async def _chat_json(system: str, user: str, model_id: str | None,
                     max_tokens: int, temperature: float) -> dict:
    """带自动重试的 JSON 生成：reasoning 模型偶尔输出非法 JSON，失败后降温重试一次"""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    last_err = None
    for attempt, temp in enumerate((temperature, max(0.1, temperature - 0.3))):
        try:
            raw = await llm.chat(messages, model_id=model_id, temperature=temp, max_tokens=max_tokens)
            return _safe_json(raw)
        except (llm.LLMError, ValueError) as e:
            last_err = e
    raise llm.LLMError(f"JSON 解析重试后仍失败: {last_err}")

def _safe_json(raw: str) -> dict:
    t = raw.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        raise llm.LLMError("模型未返回有效 JSON")
    t = t[start:end + 1]
    import json as _json, re
    try:
        return _json.loads(t)
    except _json.JSONDecodeError:
        pass
    # 容错清洗：去掉块注释/行注释、尾逗号、把单引号 key/值替换为双引号后再试
    cleaned = re.sub(r"/\*[\s\S]*?\*/|//[^\n\"]*", "", t)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    try:
        return _json.loads(cleaned)
    except _json.JSONDecodeError as e:
        raise llm.LLMError(f"模型返回的 JSON 无法解析（{e}），请重试") from e


# ==================== 大文件模式（海量明细数据可视化）====================

BIGDATA_GEN_SYSTEM = """你是「万能可视化工具」的资深前端工程师。任务：为一份**海量明细数据表**（数万至数十万行）生成单文件可视化 HTML。

## 架构约定（必须严格遵守，违者即废稿）
明细数据**不在** HTML 里，也不可能塞进 HTML。数据供给协议如下：
1. 后端会在 </head> 前注入：`<script>window.PAGE_DATA = {真实聚合统计JSON}; window.__REC_ID__ = "记录ID";</script>`
   - PAGE_DATA 含：total（真实总条数）、headers（列名）、carriers（分布字典）、sources（分布字典）、segments（号段分布字典）、columns（列名数组）
2. 页面所有数字（Hero 大数字、图表、标签页计数）**只能从 window.PAGE_DATA 读取/计算**，禁止硬编码任何数量。
3. 明细表必须实现分页查询，调用后端接口：
   `GET /api/records/${window.__REC_ID__}/data?page=1&size=100&carrier=全部&source=全部&keyword=`
   返回 JSON：{ total, page, size, rows: [[...单元格...]], headers }
   - 实现 loadPage(page) 函数：fetch 上述接口（carrier/source 取当前激活的筛选值），渲染表格（用 headers 对齐列）+ 显示「第 x-y 条 / 共 total 条」+ 上一页/下一页/跳转按钮。
   - 筛选标签页（运营商/数据来源）切换时重置到第 1 页并带参重新请求。
4. 图表用 ECharts CDN 渲染 PAGE_DATA 的真实分布（如 carriers 饼图、sources 条形图、segments 条形图），图例/标签用真实类别名。

## 视觉要求
- 沿用高质感标准：CSS 设计令牌（--bg/--surface/--primary/--accent/--radius/--shadow）、
  字体层级分明（Hero 大数字 clamp(40px,6vw,64px) + tabular-nums）、克制配色、渐变强调、卡片多层阴影。
- Hero 区：大数字展示 PAGE_DATA.total（用 toLocaleString 千分位格式化），副标题说明数据覆盖范围。
- 【动效（必须实现）】
  a. 入场：Hero 指标卡依次淡入上移（animation-delay 阶梯 0.08s）；
  b. 大数字 count-up：rAF 实现 1.2s ease-out 滚动到真实值（起点从 PAGE_DATA 读取，禁止编造中间值）；
  c. 滚动显现：IntersectionObserver 给图表区/表格区加 .reveal（opacity+translateY 过渡 0.6s）；
  d. 卡片 hover 上浮 + 阴影过渡；表格行 hover 高亮背景；
  e. ECharts animationDuration 900 + cubicOut，容器切换标签页时图表 resize；
  f. 尊重 prefers-reduced-motion。
- 明细表加载显示骨架屏（shimmer 动画）；接口失败显示错误提示与重试按钮。
- 打印样式：@media print {{ .no-print {{display:none}} * {{print-color-adjust:exact}} 
  thead {{display: table-header-group}} tr {{page-break-inside: avoid}} }}
- 中文系统字体栈；max-width 1100px 居中；所有 CSS 内联；ECharts CDN：https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js

## 输出要求
- 只输出完整 HTML（<!DOCTYPE html> 到 </html>），不要解释，不要 markdown 围栏。
- 除 PAGE_DATA 提供的数据外，页面中不得出现任何编造的数量数字。"""


async def generate_html_bigdata(doc_text: str, meta: dict, stats: dict,
                                theme: str = "auto", model_id: str | None = None,
                                extra_req: str = "") -> dict:
    """大文件模式：LLM 生成框架，数字全部来自 PAGE_DATA 协议"""
    stats_brief = {
        "total": stats["total"], "headers": stats["headers"], "col_map": stats["col_map"],
        "carriers": stats["carriers"], "sources": stats["sources"], "segments": stats["segments"],
    }
    user_prompt = f"""【数据文件】{meta.get('file_name')} | 总条数：{stats['total']}（真实值，必须作为页面展示的总数）
【指定主题】{theme}
【附加要求】{extra_req or '无'}
【聚合统计（window.PAGE_DATA 将注入这些真实数据）】
{json.dumps(stats_brief, ensure_ascii=False)}
【表头样本（前 500 行预览，供你理解列含义）】
{doc_text[:6000]}"""
    raw = await llm.chat(
        [{"role": "system", "content": BIGDATA_GEN_SYSTEM + f"\n主题说明：{THEMES.get(theme, THEMES['auto'])}"},
         {"role": "user", "content": user_prompt}],
        model_id=model_id, temperature=0.5, max_tokens=16000)
    html_code = llm.extract_html(raw)
    return {"html_code": html_code}  # 注入在路由层完成后统一落盘


def inject_bigdata(html_code: str, rec_id: str, stats: dict) -> str:
    """把真实聚合数据与记录 ID 注入 HTML（head 前注入，兜底覆盖协议）"""
    page_data = {
        "total": stats["total"], "headers": stats["headers"], "col_map": stats["col_map"],
        "carriers": stats["carriers"], "sources": stats["sources"], "segments": stats["segments"],
        "columns": stats.get("columns", []),
    }
    inject = (f'<script>window.PAGE_DATA = {json.dumps(page_data, ensure_ascii=False)}; '
              f'window.__REC_ID__ = "{rec_id}";</script>\n</head>')
    out = html_code.replace("</head>", inject, 1)
    # 兜底：替换 LLM 可能写下的占位符
    out = out.replace("__REC_ID__", rec_id)
    return out


# ==================== PDF 导出组件（确定性注入，不依赖 LLM）====================

_EXPORT_SNIPPET = """
<style>
#uv-pdf-fab{position:fixed;right:22px;bottom:26px;z-index:99999;display:flex;align-items:center;gap:8px;
  padding:11px 20px;border:0;border-radius:999px;cursor:pointer;font-size:14px;font-weight:600;
  font-family:'PingFang SC','Microsoft YaHei',sans-serif;color:#fff;
  background:linear-gradient(135deg,#4f6ef7,#8b5cf6);box-shadow:0 6px 22px rgba(79,110,247,.45);
  transition:transform .22s,box-shadow .22s}
#uv-pdf-fab:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(79,110,247,.55)}
#uv-pdf-fab:active{transform:translateY(0)}
#uv-pdf-tip{position:fixed;left:50%;top:26px;transform:translateX(-50%) translateY(-80px);z-index:99999;
  padding:10px 22px;border-radius:10px;background:rgba(17,24,39,.92);color:#fff;font-size:13px;
  font-family:'PingFang SC','Microsoft YaHei',sans-serif;transition:transform .35s cubic-bezier(.22,.61,.36,1)}
#uv-pdf-tip.show{transform:translateX(-50%) translateY(0)}
@media print{
  #uv-pdf-fab,#uv-pdf-tip{display:none!important}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
  section,.card,[class*=card]{page-break-inside:avoid;break-inside:avoid}
  thead{display:table-header-group}
  tr{page-break-inside:avoid}
  body{width:100%!important;max-width:100%!important;margin:0!important}
}
</style>
<button id="uv-pdf-fab" data-no-print class="no-print" onclick="window.__uvExportPdf&&window.__uvExportPdf()">
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
    stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
  导出 PDF
</button>
<div id="uv-pdf-tip">正在调起打印…在弹窗中选择「另存为 PDF」即可导出</div>
<script>
window.__uvExportPdf=function(){
  var t=document.getElementById('uv-pdf-tip');t&&t.classList.add('show');
  setTimeout(function(){window.print();setTimeout(function(){t&&t.classList.remove('show')},800)},160);
};
</script>
"""


def inject_export(html_code: str) -> str:
    """把 PDF 导出悬浮按钮 + 打印样式注入生成页（幂等：已注入则跳过）"""
    if "uv-pdf-fab" in html_code:
        return html_code
    if "</body>" in html_code:
        return html_code.replace("</body>", _EXPORT_SNIPPET + "</body>", 1)
    return html_code + _EXPORT_SNIPPET
