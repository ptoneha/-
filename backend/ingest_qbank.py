# -*- coding: utf-8 -*-
# ingest_qbank.py —— 解析 .docx 题库为“每题一分片”，写入 question 表
import os, io, re, json, hashlib, uuid, shutil, subprocess, tempfile
from typing import Dict, List, Tuple, Optional
from docx import Document
from docx.text.run import Run
import psycopg
from db import get_database_url

PG_URL = os.getenv("DATABASE_URL", get_database_url())
IMG_DIR = os.getenv("QIMG_DIR", "./static/qimg")

# 正则
RE_QHEAD = re.compile(r"^\s*(\d+)[\.、]\s*[【(（]?\s*(判断题|单选题|多选题|填空题|证明题)\s*[】)）]?\s*", re.I)
RE_OPT   = re.compile(r"^\s*([A-H])[\.、\)]\s*(.+)$")
RE_ANS   = re.compile(r"^\s*答\s*案\s*[:：]\s*([A-H]+|对|错|True|False)\s*$", re.I)
RE_DIFF  = re.compile(r"^\s*难[易]程度\s*[:：]\s*(易|中|难)\s*$")
DIFF_MAP = {"易":1, "中":2, "难":3, "easy":1, "medium":2, "hard":3}

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def ensure_dir(d: str): 
    os.makedirs(d, exist_ok=True)


def _normalize_inline(text: str) -> str:
    """
    去重清洗：删除多余引号与连续重复的括号/坐标对。
    """
    if not text:
        return text
    
    t = text
    # 1. 统一 Unicode prime/各种引号
    t = t.replace("′", "'").replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
    
    # 2. 删除引号完整包裹的内容
    t = re.sub(r"(['\"])\s*(\([^)]+\))\s*\1", r"\2", t)  # '(1,3)' → (1,3)
    t = re.sub(r"(['\"])\s*(\d+)\s*\1", r"\2", t)        # '3' → 3
    
    # 3. 合并连续相同引号
    t = re.sub(r"'{2,}", "'", t)
    t = re.sub(r'"{2,}', '"', t)
    
    # 4. 终极去重：删除任何连续重复的括号内容（无论有无空格）
    #    匹配 (xxx)(xxx) 或 (xxx) (xxx)，只保留一份
    while True:
        before = t
        # 先处理紧邻重复
        t = re.sub(r'(\([^)]+\))\s*\1', r'\1', t)
        # 再处理任意空白分隔的重复
        t = re.sub(r'(\(\s*[^)]+\s*\))\s+\1', r'\1', t)
        if t == before:
            break  # 没有更多重复了
    
    # 5. 专门处理坐标格式的变体（如 (1,3) 和 (1, 3) 被认为是同一个）
    def _normalize_coords(s: str) -> str:
        return re.sub(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', r'(\1,\2)', s)
    t = _normalize_coords(t)
    
    # 6. 删除连续重复的数学环境（如 $x$$x$ 或 $$y$$$$y$$）
    #    核心问题：Pandoc 把 Word 公式识别成两份，且中间无空格
    #    策略：先标准化（加空格），再去重，最后还原
    
    # Step 1: 在所有 $ 符号后添加临时标记空格（便于反向引用匹配）
    t = re.sub(r'\$(?!\s)', '$ ', t)  # $ 后面不是空格就加空格
    
    # Step 2: 去重（现在 $x$ $x$ 可以被 \1 匹配）
    while True:
        before = t
        # 内联公式去重
        t = re.sub(r'(\$\s*[^\$]+?\s*\$)\s*\1', r'\1', t)
        # 块级公式去重
        t = re.sub(r'(\$\$\s*[^\$]+?\s*\$\$)\s*\1', r'\1', t)
        if t == before:
            break
    
    # Step 3: 移除多余的空格（还原紧凑格式）
    t = re.sub(r'\$\s+', '$', t)  # $ 后的空格删除
    
    # 7. 终极通用去重：删除任何连续重复的文本片段（至少5个字符，避免误删）
    #    例如："A = {1,2,3,4}A = {1,2,3,4}" → "A = {1,2,3,4}"
    #    策略：找到长度≥5且连续重复的子串
    def _remove_text_duplicates(s: str) -> str:
        # 使用滑动窗口查找重复
        max_attempts = 10  # 防止无限循环
        for _ in range(max_attempts):
            found = False
            # 从长到短尝试（优先删除长片段）
            for length in range(len(s) // 2, 4, -1):  # 最小5个字符
                for i in range(len(s) - length * 2 + 1):
                    chunk = s[i:i+length]
                    next_chunk = s[i+length:i+length*2]
                    # 如果两个片段完全相同（忽略首尾空格）
                    if chunk.strip() == next_chunk.strip() and len(chunk.strip()) >= 5:
                        # 删除第二个片段
                        s = s[:i+length] + s[i+length*2:]
                        found = True
                        break
                if found:
                    break
            if not found:
                break
        return s
    
    t = _remove_text_duplicates(t)
    
    return t

def save_inline_images(doc: Document, base_name: str) -> Dict[str, str]:
    """
    导出 docx 内联图片；返回 {rid: /static/qimg/xxx.png}
    """
    ensure_dir(IMG_DIR)
    mapping = {}
    # 遍历关系 part（python-docx 的图片以关系 id 引用）
    media = doc.part._rels
    for rid, rel in media.items():
        if "image" in rel.reltype:
            ext = os.path.splitext(rel.target_ref)[1] or ".png"
            fname = f"{base_name}-{uuid.uuid4().hex}{ext}"
            out_path = os.path.join(IMG_DIR, fname)
            with open(out_path, "wb") as f:
                f.write(rel.target_part.blob)
            mapping[rid] = f"/static/qimg/{fname}"
    return mapping

def para_to_markdown(p, img_map: Dict[str, str]) -> str:
    """
    把一个段落（含粗体/图片）转成简易 Markdown。
    图片以 ![](uri) 形式插入。
    """
    md = ""
    for run in p.runs:
        txt = run.text or ""
        if run.bold and txt.strip():
            txt = f"**{txt}**"
        md += txt
        # 处理该 run 上的图片（如果有）
        if run._r.xpath(".//pic:pic") or run._r.xpath(".//a:blip"):
            # 遍历所有 blip，取 r:embed
            blips = run._r.xpath(".//a:blip")
            for b in blips:
                rid = b.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                if rid and rid in img_map:
                    md += f"\n\n![]({img_map[rid]})\n\n"
    return md.strip()


# ---------- 使用 pandoc 将 docx 转为 Markdown（含 LaTeX 公式） ----------

def _which_pandoc() -> Optional[str]:
    exe = shutil.which("pandoc") or shutil.which("pandoc.exe")
    if exe:
        return exe
    for path in [
        r"C:\\Program Files\\Pandoc\\pandoc.exe",
        r"C:\\Program Files (x86)\\Pandoc\\pandoc.exe",
    ]:
        if os.path.exists(path):
            return path
    return None


def _pandoc_docx_to_markdown_with_media(path: str) -> Optional[str]:
    pandoc = _which_pandoc()
    if not pandoc:
        return None
    ensure_dir(IMG_DIR)
    with tempfile.TemporaryDirectory() as td:
        md_out = os.path.join(td, "out.md")
        cmd = [
            pandoc,
            path,
            "-t",
            # 使用 markdown 而非 gfm，关闭 smart 和 raw_html，启用 tex_math_dollars
            "markdown-smart-raw_html+tex_math_dollars",
            "--wrap=none",
            "--extract-media",
            td,
            "-o",
            md_out,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0 or not os.path.exists(md_out):
            return None
        with open(md_out, "r", encoding="utf-8") as f:
            md = f.read()

        mapping: Dict[str, str] = {}
        media_root = os.path.join(td, "media")
        if os.path.exists(media_root):
            for root, _dirs, files in os.walk(media_root):
                for name in files:
                    src = os.path.join(root, name)
                    ext = os.path.splitext(name)[1] or ".png"
                    new_name = f"{uuid.uuid4().hex}{ext}"
                    dst = os.path.join(IMG_DIR, new_name)
                    shutil.move(src, dst)
                    rel = os.path.relpath(src, td).replace("\\", "/")
                    mapping[rel] = f"/static/qimg/{new_name}"

        def repl(m):
            p = m.group(1)
            return f"]({mapping.get(p, p)})"

        md = re.sub(r"\]\((media/[^)]+)\)", repl, md)
        return md


def _parse_markdown_questions(md: str) -> List[Dict]:
    lines = [_normalize_inline(ln.rstrip()) for ln in md.splitlines()]
    qs: List[Dict] = []
    cur: Dict = {}

    def flush():
        nonlocal cur
        if not cur:
            return
        stem = "\n".join(cur.get("stem_parts", [])).strip()
        expl = "\n".join(cur.get("expl_parts", [])).strip()
        options = cur.get("options", {})
        qtype = cur.get("qtype", "unknown")
        answer = cur.get("answer_text")
        diff = cur.get("difficulty", 2)
        tags = cur.get("tags", [])
        canon = stem + "\n" + json.dumps(options, ensure_ascii=False) + "\n" + (answer or "") + "\n" + expl
        sha = sha256_text(canon)
        qs.append({
            "qtype": qtype,
            "stem_md": stem,
            "options_json": options or None,
            "answer_text": answer,
            "explanation_md": expl or None,
            "tags": tags or None,
            "difficulty": diff,
            "sha256": sha
        })
        cur = {}

    for raw in lines:
        text = (raw or "").strip()
        if not text:
            continue
        m = RE_QHEAD.match(text)
        if m:
            flush()
            _qno, qtype_cn = m.groups()
            qtype = {"判断题":"judge","单选题":"single","多选题":"multiple","填空题":"fill","证明题":"proof"}.get(qtype_cn, "other")
            cur = {"qtype": qtype, "stem_parts": [text], "options": {}, "expl_parts": [], "difficulty": 2, "tags": []}
            continue

        if cur:
            mopt = RE_OPT.match(text)
            mans = RE_ANS.match(text)
            mdif = RE_DIFF.match(text)
            if mopt:
                k, _v = mopt.groups()
                cur["options"][k] = _normalize_inline(mopt.group(2).strip())
            elif mans:
                cur["answer_text"] = mans.group(1).strip().upper().replace("对","True").replace("错","False")
            elif mdif:
                cur["difficulty"] = DIFF_MAP.get(mdif.group(1), 2)
            else:
                if text.startswith(("解析：","解：","【解析】")):
                    cur.setdefault("_in_expl", True)
                    content = text.split("：",1)[-1] if "：" in text else text
                    cur["expl_parts"].append(_normalize_inline(content))
                else:
                    if cur.get("_in_expl"):
                        cur["expl_parts"].append(_normalize_inline(text))
                    else:
                        cur["stem_parts"].append(_normalize_inline(text))

    flush()
    return qs

def parse_docx_questions(path: str) -> List[Dict]:
    # 优先尝试 pandoc（可将 OMML 公式转换为 LaTeX）
    md = _pandoc_docx_to_markdown_with_media(path)
    if md:
        return _parse_markdown_questions(md)

    doc = Document(path)
    base = os.path.splitext(os.path.basename(path))[0]
    img_map = save_inline_images(doc, base)

    qs: List[Dict] = []
    cur: Dict = {}

    def flush():
        nonlocal cur
        if not cur: return
        stem = "\n".join(cur.get("stem_parts", [])).strip()
        expl = "\n".join(cur.get("expl_parts", [])).strip()
        options = cur.get("options", {})
        qtype = cur.get("qtype", "unknown")
        # 修正：答案字段应为 answer_text
        answer = cur.get("answer_text")
        diff = cur.get("difficulty", 2)
        tags = cur.get("tags", [])
        canon = stem + "\n" + json.dumps(options, ensure_ascii=False) + "\n" + (answer or "") + "\n" + expl
        sha = sha256_text(canon)
        qs.append({
            "qtype": qtype,
            "stem_md": stem,
            "options_json": options or None,
            "answer_text": answer,
            "explanation_md": expl or None,
            "tags": tags or None,
            "difficulty": diff,
            "sha256": sha
        })
        cur = {}

    for p in doc.paragraphs:
        text = _normalize_inline((p.text or "").strip())
        md = _normalize_inline(para_to_markdown(p, img_map))
        if not text and not md: 
            continue

        # 新题开头： 1.【判断题】……
        m = RE_QHEAD.match(text)
        if m:
            flush()
            qno, qtype_cn = m.groups()
            qtype = {"判断题":"judge","单选题":"single","多选题":"multiple","填空题":"fill","证明题":"proof"}.get(qtype_cn, "other")
            cur = {"qtype": qtype, "stem_parts": [md], "options": {}, "expl_parts": [], "difficulty": 2, "tags": []}
            continue

        # 在题干/选项/答案/解析之间切换
        if cur:
            mopt = RE_OPT.match(text)   # 选项
            mans = RE_ANS.match(text)   # 答案
            mdif = RE_DIFF.match(text)  # 难度
            if mopt:
                k, v = mopt.groups()
                cur["options"][k] = _normalize_inline(mopt.group(2).strip())
                continue
            elif mans:
                cur["answer_text"] = mans.group(1).strip().upper().replace("对","True").replace("错","False")
                continue
            elif mdif:
                cur["difficulty"] = DIFF_MAP.get(mdif.group(1), 2)
                continue
            else:
                # 解析的启发式：遇到以“解析：”“解：”开头，之后都进解析区
                if text.startswith(("解析：","解：","【解析】")):
                    cur.setdefault("_in_expl", True)
                    content = md.split("：",1)[-1] if "：" in md else md
                    cur["expl_parts"].append(_normalize_inline(content))
                else:
                    if cur.get("_in_expl"):
                        cur["expl_parts"].append(_normalize_inline(md))
                    else:
                        cur["stem_parts"].append(_normalize_inline(md))
        else:
            # 文档前言/空段落，忽略
            pass

    flush()
    return qs

def insert_questions(rows: List[Dict], source_file: str) -> int:
    if not rows: return 0
    inserted = 0
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            for r in rows:
                try:
                    cur.execute("""
                      INSERT INTO question(qtype, stem_md, options_json, answer_text, explanation_md,
                                           tags, difficulty, source_file, sha256)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      ON CONFLICT (sha256) DO NOTHING
                    """, (r["qtype"], r["stem_md"], json.dumps(r["options_json"], ensure_ascii=False) if r["options_json"] else None,
                          r.get("answer_text"), r.get("explanation_md"),
                          r.get("tags"), r.get("difficulty"), source_file, r["sha256"]))
                    inserted += 1
                except Exception as e:
                    print("skip one:", e)
        conn.commit()
    return inserted

def main():
    import sys
    if len(sys.argv) < 2:
        print("用法: python ingest_qbank.py /path/to/题库.docx"); return
    path = sys.argv[1]
    rows = parse_docx_questions(path)
    n = insert_questions(rows, os.path.basename(path))
    print(f"[OK] {os.path.basename(path)} 导入 {n} 题（含图片引用） -> question 表")

if __name__ == "__main__":
    main()
