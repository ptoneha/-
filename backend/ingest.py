import hashlib
import re
from io import BytesIO
from typing import List, Dict, Any, Tuple

from docx import Document

from db import get_conn, release_conn, _execute, _query_one


H1_RE = re.compile(r"^第[一二三四五六七八九十百千万0-9]+节")
H2_RE = re.compile(r"^[一二三四五六七八九十]+、\s*")


def canonicalize_text(text: str) -> str:
    if not text:
        return text
    rep = (
        ("→", "->"),
        ("∞", "inf"),
        ("（", "("), ("）", ")"),
        ("／", "/"), ("∕", "/"), ("/", "/"),
        ("·", "*"),
    )
    t = text
    for a, b in rep:
        t = t.replace(a, b)
    return t


def to_plain(text: str) -> str:
    if not text:
        return text
    # 移除 $ 和 $$ 包裹，仅保留内部内容
    t = re.sub(r"\$\$(.+?)\$\$", r"\1", text, flags=re.S)
    t = re.sub(r"\$(.+?)\$", r"\1", t, flags=re.S)
    return t


def classify_kind(text: str) -> str:
    t = text or ""
    if any(k in t for k in ["定义", "ε–δ", "ε–N", "ε-δ", "ε-N"]):
        return "definition"
    if any(k in t for k in ["定理", "准则", "引理", "推论"]):
        return "theorem"
    if any(k in t for k in ["重要极限", "等价无穷小", "公式", "恒等式"]):
        return "formula"
    if any(k in t for k in ["性质", "连续", "间断"]):
        return "property"
    if any(k in t for k in ["例题", "例", "计算", "求", "证明"]):
        return "example"
    return "remark"


def split_with_overlap(text: str, max_len: int = 1200, overlap: int = 120) -> List[str]:
    if len(text) <= max_len:
        return [text]
    parts = []
    start = 0
    while start < len(text):
        end = start + max_len
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return parts


def parse_docx(file_bytes: bytes) -> Dict[str, Any]:
    doc = Document(BytesIO(file_bytes))
    heading_h1 = None
    sections: List[Tuple[str, str]] = []  # (h2_title, content)
    cur_h2: str = ""
    buf: List[str] = []

    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue
        if H1_RE.match(text) and heading_h1 is None:
            heading_h1 = text
            continue
        if H2_RE.match(text):
            # flush previous
            if cur_h2:
                sections.append((cur_h2, "\n".join(buf).strip()))
            cur_h2 = text
            buf = []
        else:
            buf.append(text)

    if cur_h2:
        sections.append((cur_h2, "\n".join(buf).strip()))

    # 若未检测到任何 H2，则将正文作为单一分片回退
    fallback = None
    if not sections:
        fallback = "\n".join(buf).strip()

    return {"h1": heading_h1, "sections": sections, "fallback": fallback}


def _cn_num_to_int(s: str) -> int:
    # 极简中文数字转换：支持到 99
    mapping = {"零":0,"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
    if not s:
        return 0
    # 直接包含阿拉伯数字
    if re.search(r"\d+", s):
        return int(re.search(r"\d+", s).group())
    # 十/二十/三十五
    if s == "十":
        return 10
    if s.endswith("十"):
        # 二十 三十
        return mapping.get(s[:-1], 0) * 10
    if "十" in s:
        a, b = s.split("十", 1)
        tens = mapping.get(a, 1)  # "十X" -> 1X
        ones = mapping.get(b, 0)
        return tens * 10 + ones
    # 个位数
    return mapping.get(s, 0)


def _extract_section_from_h1(h1: str) -> int:
    if not h1:
        return 0
    m = re.match(r"^第([一二三四五六七八九十百千万0-9]+)节", h1)
    if not m:
        return 0
    return _cn_num_to_int(m.group(1))


def process_upload(file_bytes: bytes, filename: str, chapter: int, section_number: int, source: str = "kb") -> Dict[str, Any]:
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    parsed = parse_docx(file_bytes)
    h1 = parsed.get("h1") or filename
    sections: List[Tuple[str, str]] = parsed.get("sections", [])
    fallback: str = parsed.get("fallback") or ""
    # 若用户未调整默认 1，但 H1 能解析出非 1 的节号，则自动采用 H1 的节号
    inferred_sec = _extract_section_from_h1(h1)
    if section_number in (None, 0, 1) and inferred_sec not in (0, 1):
        section_number = inferred_sec

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # 查重：若已存在 doc
                cur.execute("SELECT doc_id FROM public.doc WHERE sha256 = %s", (sha256,))
                row = cur.fetchone()
                if row:
                    doc_id = row[0]
                else:
                    cur.execute(
                        """
                        INSERT INTO public.doc (title, chapter, section_number, source_filename, source, sha256)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING doc_id
                        """,
                        (h1, chapter, section_number, filename, source, sha256),
                    )
                    doc_id = cur.fetchone()[0]

                # 如果此前因为没有 H2 导致没有分片，这里允许补录
                cur.execute("SELECT COUNT(1) FROM public.chunk WHERE doc_id = %s", (doc_id,))
                existing = cur.fetchone()[0]

                inserted = 0

                if existing == 0:
                    # 若没有 H2，则以“正文”整体入库
                    if not sections and fallback:
                        sections = [("正文", fallback)]

                    for idx, (h2, content) in enumerate(sections, start=1):
                        if not content:
                            continue
                        parts = split_with_overlap(content)
                        for p_idx, part in enumerate(parts, start=1):
                            content_md = part
                            content_plain = to_plain(content_md)
                            canonical = canonicalize_text(content_md)
                            kind = classify_kind(part)
                            anchor = f"ch{chapter}-s{section_number}-h2-{idx}"
                            if len(parts) > 1:
                                anchor += f"-p{p_idx}"

                            cur.execute(
                                """
                                INSERT INTO public.chunk (
                                  doc_id, kind, heading_h1, heading_h2, anchor,
                                  content_md, content_plain, canonical, tokens
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING chunk_id
                                """,
                                (
                                    doc_id,
                                    kind,
                                    h1,
                                    h2,
                                    anchor,
                                    content_md,
                                    content_plain,
                                    canonical,
                                    len(content_plain or ""),
                                ),
                            )
                            _ = cur.fetchone()[0]
                            inserted += 1

        return {"doc_id": doc_id, "chunks": inserted}
    finally:
        release_conn(conn)


