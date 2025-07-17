import re
import pytesseract
from pdf2image import convert_from_path

# ---------------------------
# Resume keyword fallback
# ---------------------------
RESUME_SECTIONS = [
    "education", "skills", "experience", "projects",
    "certifications", "extracurricular", "achievements",
    "summary", "profile", "contact"
]

# Regexes for numbered headings
RE_H1_NUM = re.compile(r"^\s*(\d+|[IVXLCDM]+)[\.\)]?\s", re.IGNORECASE)           # 1. ... or I. ...
RE_H2_NUM = re.compile(r"^\s*\d+\.\d+[\.\)]?\s")                                  # 2.1 ...
RE_H3_NUM = re.compile(r"^\s*\d+\.\d+\.\d+[\.\)]?\s")                             # 3.2.1 ...

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# ---------------------------
# OCR fallback
# ---------------------------
def extract_text_ocr(pdf_path: str) -> str:
    try:
        images = convert_from_path(pdf_path)
        text = []
        for img in images:
            text.append(pytesseract.image_to_string(img))
        return "\n".join(text)
    except Exception:
        return ""


# ---------------------------
# Flatten text from PyMuPDF doc
# ---------------------------
def flatten_text_doc(doc) -> str:
    """Return plain text from all pages (PyMuPDF doc)."""
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    return "\n".join(parts)


# ---------------------------
# General (multi-purpose) heading detection
# Uses: numbered patterns, font size ranking, bold signal, shortness
# ---------------------------
def detect_headings_general(doc):
    """
    Multi-purpose heading detector for structured docs:
    - Recognizes numbered headings (1., 2.1, 3.2.1)
    - Uses font size ranks: largest=H1, next=H2, next=H3
    - Bold + shortness boost
    - Keeps multiple headings per page (no suppression)
    """
    candidates = []   # raw spans collapsed per line
    all_sizes = []

    for page_idx, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text_parts = []
                max_size = 0.0
                any_bold = False
                for span in line["spans"]:
                    txt = span["text"]
                    if not txt.strip():
                        continue
                    line_text_parts.append(txt)
                    sz = span["size"]
                    max_size = max(max_size, sz)
                    if span["flags"] & 2:
                        any_bold = True
                if not line_text_parts:
                    continue
                line_text = _normalize("".join(line_text_parts))
                if not line_text:
                    continue

                candidates.append({
                    "text": line_text,
                    "size": max_size,
                    "bold": any_bold,
                    "page": page_idx
                })
                all_sizes.append(max_size)

    if not candidates:
        return []

    # Rank font sizes
    unique_sizes = sorted(set(all_sizes), reverse=True)
    size_to_rank = {sz: i for i, sz in enumerate(unique_sizes)}  # 0=largest

    outline = []
    for cand in candidates:
        txt = cand["text"]
        size = cand["size"]
        page = cand["page"]
        bold = cand["bold"]

        # Score
        score = 0

        # Numbered patterns override font (semantic)
        if RE_H3_NUM.match(txt):
            outline.append({"level": "H3", "text": txt, "page": page})
            continue
        if RE_H2_NUM.match(txt):
            outline.append({"level": "H2", "text": txt, "page": page})
            continue
        if RE_H1_NUM.match(txt):
            outline.append({"level": "H1", "text": txt, "page": page})
            continue

        # Font size rank heuristic
        rank = size_to_rank.get(size, 999)
        if rank == 0:
            score += 5
        elif rank == 1:
            score += 3
        elif rank == 2:
            score += 1

        # Bold boost
        if bold:
            score += 1

        # Shortness boost (common in headings)
        if len(txt.split()) <= 10:
            score += 1

        # Classify by score
        if score >= 5:
            level = "H1"
        elif score >= 3:
            level = "H2"
        elif score >= 2:
            level = "H3"
        else:
            continue

        outline.append({"level": level, "text": txt, "page": page})

    # Deduplicate identical heading text on same page (keep first)
    seen = set()
    deduped = []
    for h in outline:
        key = (h["text"].lower().strip(), h["page"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(h)

    return deduped


# ---------------------------
# Resume fallback detection
# doc may be None when called on OCR text
# ---------------------------
def detect_headings_resume(doc, text: str):
    """
    Heading detection for resumes based on keyword prefixes.
    Uses text passed in; doc only for page association (optional).
    """
    # Map page by scanning doc pages if available; fallback page=1
    page_lookup = {}
    if doc is not None:
        for pnum, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            page_lookup[pnum] = page_text

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    heads = []
    for ln in lines:
        clean = re.sub(r"[^a-zA-Z ]", "", ln).strip().lower()
        for section in RESUME_SECTIONS:
            if clean.startswith(section):
                # try to locate page
                page = 1
                if page_lookup:
                    for pnum, ptext in page_lookup.items():
                        if ln in ptext:
                            page = pnum
                            break
                heads.append({"level": "H1", "text": ln, "page": page})
                break
    return heads
