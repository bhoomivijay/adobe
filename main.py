import os
import json
import fitz  # PyMuPDF
from utils import detect_headings_general, detect_headings_resume, flatten_text_doc, extract_text_ocr

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def choose_title(doc, headings, flat_text):
    """
    Title priority:
    1. First H1 heading
    2. PDF metadata title
    3. First non-empty text line from page 1 / flattened text
    4. "Untitled Document"
    """
    # 1. First H1
    for h in headings:
        if h["level"] == "H1":
            return h["text"].strip()

    # 2. Metadata
    meta_title = (doc.metadata or {}).get("title")
    if meta_title and meta_title.strip():
        return meta_title.strip()

    # 3. First line from page 1 text
    try:
        p0_text = doc[0].get_text("text").strip()
        if p0_text:
            first_line = p0_text.split("\n", 1)[0].strip()
            if first_line:
                return first_line
    except Exception:
        pass

    # 4. Flattened text fallback
    if flat_text:
        first_line = flat_text.split("\n", 1)[0].strip()
        if first_line:
            return first_line

    return "Untitled Document"


def extract_outline(pdf_path):
    # Open doc
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return {"title": "Untitled Document", "outline": []}

    if len(doc) == 0:
        return {"title": "Untitled Document", "outline": []}

    # Flattened text (PyMuPDF)
    flat_text = flatten_text_doc(doc)

    # General heading detection (font + regex + bold)
    headings = detect_headings_general(doc)

    # If no headings found, try resume heuristic
    if not headings:
        resume_heads = detect_headings_resume(doc, flat_text)
        headings = resume_heads

    # If *still* nothing and NO text came from PyMuPDF, OCR fallback
    if not headings and not flat_text.strip():
        print("⚠ No text extracted by PyMuPDF; attempting OCR fallback ...")
        ocr_text = extract_text_ocr(pdf_path)
        if ocr_text.strip():
            headings = detect_headings_resume(None, ocr_text)  # try resume keys on OCR text
            if not headings:  # last resort: no outline
                flat_text = ocr_text

    # Choose title
    title = choose_title(doc, headings, flat_text)

    # Remove title duplication from outline
    cleaned_outline = [h for h in headings if h["text"].strip() != title.strip()]

    return {"title": title, "outline": cleaned_outline}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, file)
            print(f"Processing {file}...")
            result = extract_outline(pdf_path)
            out_name = os.path.splitext(file)[0] + ".json"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Output saved to {out_path}")


if __name__ == "__main__":
    main()
