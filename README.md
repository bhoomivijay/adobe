# Multi-Purpose PDF Outline Extractor

Extracts document structure (Title, H1, H2, H3) from PDFs.

### Features
- Works on **reports, manuals, syllabi** (font + numbering + bold heuristics).
- Handles **resumes** via keyword fallback.
- **OCR fallback** for difficult/image PDFs (offline; uses Tesseract).
- Outputs JSON:
```json
{
  "title": "Document Title",
  "outline": [
    {"level": "H1", "text": "Section", "page": 1},
    {"level": "H2", "text": "Subsection", "page": 2}
  ]
}
