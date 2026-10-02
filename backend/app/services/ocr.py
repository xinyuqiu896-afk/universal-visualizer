"""图片 OCR 服务：基于 Agnes 视觉模型，支持长图切片有序合并、低清图片增强预处理"""
import base64, io, asyncio, re
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from . import llm

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

# ---- 长图切片参数 ----
LONG_RATIO = 2.2          # 高/宽 >= 2.2 视为长图
LONG_MIN_H = 2600         # 或高度超过 2600px 视为长图
CHUNK_H = 1500            # 每片高度
OVERLAP = 200             # 相邻切片重叠高度（防文字被切断漏识）

# ---- 低清增强参数 ----
LOW_RES_W = 720           # 宽度低于此值视为低清
UPSCALE_MIN_W = 1400      # 增强后目标最小宽度

OCR_PROMPT = """你是高精度 OCR 引擎。逐字识别图片中的全部文字，严格遵守：
1. 按原始阅读顺序（从上到下、从左到右）输出纯文本，**每一行都必须完整输出，禁止省略或截断**。
2. 不要输出任何解释、标注、行号、表情或"以下是识别结果"之类的开场白。
3. 保留原始换行；表格内容用" | "分隔单元格，每行一条。
4. 数字、标点、中英文严格逐位照原文输出；确实模糊看不清的字用"□"占位，禁止猜测编造。"""

# 切片最小宽度：过窄的切片会被视觉模型整体缩放导致小字难辨，垫白边增强
MIN_SLICE_W = 640


def _to_b64(img: Image.Image) -> str:
    """OCR 一律用 PNG 无损编码（JPEG 压缩伪影会显著伤害小字识别）"""
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _pad_width(img: Image.Image) -> Image.Image:
    """窄图垫白边到最小宽度，降低长宽比、提升视觉模型识别分辨率"""
    w, h = img.size
    if w >= MIN_SLICE_W:
        return img
    canvas = Image.new("RGB", (MIN_SLICE_W, h), "white")
    canvas.paste(img.convert("RGB"), ((MIN_SLICE_W - w) // 2, 0))
    return canvas


async def _ocr_one(img: Image.Image, model_id: str | None, note: str = "") -> list[str]:
    """单张图片 OCR，返回文本行列表（视觉偶发失效自动重试，最多 3 次）"""
    b64 = _to_b64(_pad_width(img))
    prompt = OCR_PROMPT + (f"\n（说明：{note}）" if note else "")
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]
    refusal = re.compile(r"无法看到|看不到|无法识别|无法查看|请上传|请提供|没有图片|不能识别|无法访问|未能识别")
    result: list[str] = []
    for attempt in range(3):
        try:
            raw = await llm.chat([{"role": "user", "content": content}],
                                 model_id=model_id, temperature=0.1, max_tokens=10000, timeout=300)
        except llm.LLMError:
            if attempt == 2:
                raise
            continue
        lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
        if lines and not refusal.search(raw[:200]):
            return lines
        result = lines  # 保留最后一次结果兜底
    return result


def _enhance_lowres(img: Image.Image) -> Image.Image:
    """低清增强：放大到目标宽度 + 灰度自适应对比 + 锐化"""
    w, h = img.size
    scale = max(2.0, UPSCALE_MIN_W / max(w, 1))
    img = img.convert("L")
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=140, threshold=2))
    return img


def _merge_slices(parts: list[list[str]]) -> list[str]:
    """有序合并切片 OCR 结果，按行去重相邻切片重叠区域（最长后缀-前缀匹配）"""
    merged: list[str] = []
    for part in parts:
        if not merged:
            merged = list(part)
            continue
        # 在前片尾部与后片头部之间找最大重叠行数
        max_check = min(len(merged), len(part), 30)
        best = 0
        for k in range(max_check, 0, -1):
            if merged[-k:] == part[:k]:
                best = k
                break
        merged += part[best:]
    # 全局去重（连续重复行，保留一处；跳过短行避免误删）
    out: list[str] = []
    for ln in merged:
        if len(ln) > 4 and out and out[-1] == ln:
            continue
        out.append(ln)
    return out


async def ocr_image(path: str, model_id: str | None = None, progress_cb=None) -> dict:
    """图片 OCR 主入口：自动识别长图/低清并相应处理，返回 {text, meta}"""
    p = Path(path)
    img = Image.open(p)
    img.load()
    if img.mode in ("P", "CMYK"):
        img = img.convert("RGB")
    w, h = img.size
    meta = {"file_name": p.name, "ext": p.suffix.lower().lstrip("."),
            "width": w, "height": h, "ocr": True}

    # 低清增强
    if w < LOW_RES_W and h < 6000:
        img = _enhance_lowres(img)
        meta["enhanced"] = True
        meta["enhanced_size"] = list(img.size)

    is_long = (h / max(w, 1) >= LONG_RATIO) or (h > LONG_MIN_H)
    if not is_long:
        lines = await _ocr_one(img, model_id)
        meta["long_image"] = False
        text = "\n".join(lines)
    else:
        # 长图切片：按序并行 OCR（限并发 3 保序），重叠区按行去重合并
        n_slices = max(1, -(-(h - OVERLAP) // (CHUNK_H - OVERLAP)))
        slices = []
        step = CHUNK_H - OVERLAP
        for i in range(n_slices):
            top = i * step
            box = (0, top, w, min(top + CHUNK_H, h))
            if box[3] - box[1] < 40:
                continue
            slices.append(img.crop(box))
        meta["long_image"] = True
        meta["slices"] = len(slices)
        sem = asyncio.Semaphore(3)

        async def run(idx, sl):
            async with sem:
                if progress_cb:
                    progress_cb(idx + 1, len(slices))
                return idx, await _ocr_one(sl, model_id, note=f"长图第{idx+1}/{len(slices)}段，只识别本段内容")

        results = await asyncio.gather(*[run(i, s) for i, s in enumerate(slices)])
        results.sort(key=lambda x: x[0])
        lines = _merge_slices([r[1] for r in results])
        text = "\n".join(lines)

    meta["char_count"] = len(text)
    if not text.strip():
        raise llm.LLMError("未识别出文字内容（可能为纯图片/图表，无可提取文本）")
    return {"text": text, "meta": meta}
