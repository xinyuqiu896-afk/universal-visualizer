"""多格式文件解析引擎：docx / pptx / pdf / txt / md / csv / xlsx / json / html / zip -> 纯文本"""
import zipfile
from pathlib import Path

def parse_file(path: str) -> dict:
    """返回 {text, meta}，meta 含页数/段落数等统计"""
    p = Path(path)
    ext = p.suffix.lower()
    parsers = {
        ".docx": _parse_docx, ".doc": _parse_docx,
        ".pptx": _parse_pptx,
        ".pdf": _parse_pdf,
        ".txt": _parse_text, ".md": _parse_text, ".json": _parse_text,
        ".html": _parse_html, ".htm": _parse_html,
        ".csv": _parse_csv, ".xlsx": _parse_xlsx, ".xls": _parse_xlsx,
    }
    fn = parsers.get(ext)
    if not fn:
        raise ValueError(f"暂不支持解析的格式: {ext}")
    text, meta = fn(p)
    text = (text or "").strip()
    meta.update(file_name=p.name, ext=ext, size_kb=round(p.stat().st_size / 1024, 1),
                char_count=len(text))
    return {"text": text, "meta": meta}

def parse_zip(path: str) -> dict:
    """压缩包通道：提取 zip 内可解析文档逐个解析并拼接（处理中文文件名编码）"""
    p = Path(path)
    inner_parsed, skipped, parts = [], [], []
    parsers = {".docx": _parse_docx, ".doc": _parse_docx, ".pptx": _parse_pptx,
               ".pdf": _parse_pdf, ".txt": _parse_text, ".md": _parse_text,
               ".json": _parse_text, ".html": _parse_html, ".htm": _parse_html,
               ".csv": _parse_csv, ".xlsx": _parse_xlsx, ".xls": _parse_xlsx}
    with zipfile.ZipFile(p) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # 中文名修复：Windows 打包常用 GBK，zipfile 默认按 cp437 解码
            name = info.filename
            if not (info.flag_bits & 0x800):  # 未置 UTF-8 标志位，按 GBK 修复
                try:
                    name = name.encode("cp437").decode("gbk")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
            ext = Path(name).suffix.lower()
            if ext not in parsers:
                if not name.startswith("__MACOSX"):
                    skipped.append(name)
                continue
            if info.file_size > 8 * 1024 * 1024:
                skipped.append(f"{name}（超 8MB）")
                continue
            tmp = p.parent / f"_zip_{uuid4hex()}_{Path(name).name}"
            tmp.write_bytes(zf.read(info))
            try:
                r = parse_file(str(tmp))
                parts.append(f"===== {name} =====\n{r['text']}")
                inner_parsed.append(name)
            except Exception:
                skipped.append(name)
            finally:
                tmp.unlink(missing_ok=True)
    text = "\n\n".join(parts).strip()
    if not inner_parsed:
        raise ValueError("压缩包内没有可解析的文档（支持 docx/pptx/pdf/txt/md/csv/xlsx/json/html）")
    meta = {"inner_files": inner_parsed, "inner_count": len(inner_parsed)}
    if skipped:
        meta["skipped"] = skipped
    return {"text": text, "meta": meta}

def uuid4hex() -> str:
    import uuid
    return uuid.uuid4().hex[:8]

def _parse_docx(p):
    from docx import Document
    doc = Document(str(p))
    parts = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            style = para.style.name if para.style else ""
            if style.lower().startswith("heading"):
                level = "".join(ch for ch in style if ch.isdigit()) or "2"
                parts.append("#" * int(level) + " " + t)
            else:
                parts.append(t)
    for i, table in enumerate(doc.tables, 1):
        rows = [" | ".join(c.text.strip() for c in r.cells) for r in table.rows]
        if rows:
            parts.append(f"\n[表格{i}]\n" + "\n".join(rows))
    return "\n\n".join(parts), {"paragraphs": len(doc.paragraphs), "tables": len(doc.tables)}

def _parse_pptx(p):
    from pptx import Presentation
    prs = Presentation(str(p))
    parts = []
    for idx, slide in enumerate(prs.slides, 1):
        parts.append(f"\n===== 第 {idx} 页 =====")
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = "".join(run.text for run in para.runs).strip()
                    if t:
                        parts.append(t)
            if shape.has_table:
                for r in shape.table.rows:
                    parts.append(" | ".join(c.text.strip() for c in r.cells))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                parts.append(f"[备注] {note}")
    return "\n".join(parts), {"slides": len(prs.slides)}

def _parse_pdf(p):
    import pdfplumber
    parts = []
    with pdfplumber.open(str(p)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            parts.append(f"\n===== 第 {i} 页 =====")
            txt = page.extract_text() or ""
            parts.append(txt)
            for t in page.extract_tables():
                for r in t:
                    parts.append(" | ".join(str(c or "") for c in r))
    return "\n".join(parts), {"pages": len(parts) // 1}

def _parse_text(p):
    return p.read_text(encoding="utf-8", errors="ignore"), {}

def _parse_html(p):
    import re
    raw = p.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", raw, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", raw)
    text = re.sub(r"\n{2,}", "\n", text)
    return text, {}

def _parse_csv(p):
    import csv
    rows = []
    with open(p, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        for i, row in enumerate(csv.reader(f)):
            rows.append(" | ".join(row))
            if i >= 800:
                rows.append("...(数据过长已截断)")
                break
    return "\n".join(rows), {"rows": len(rows)}

def _parse_xlsx(p):
    from openpyxl import load_workbook
    wb = load_workbook(str(p), read_only=True, data_only=True)
    parts = []
    for ws in wb.worksheets:
        parts.append(f"\n===== 工作表: {ws.title} =====")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            parts.append(" | ".join("" if c is None else str(c) for c in row))
            if i >= 500:
                parts.append("...(数据过长已截断)")
                break
    wb.close()
    return "\n".join(parts), {"sheets": len(wb.sheetnames)}
