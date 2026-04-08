"""Extract text and skills from uploaded resumes."""

import io
import re
import base64
from .profile import ALL_SKILLS


def parse_resume_pdf(uploaded_file) -> str:
    """Extract text from an uploaded PDF file using pdfplumber."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def render_resume_preview_png(uploaded_file) -> bytes | None:
    """Render first PDF page into a PNG image for stable preview layout."""
    try:
        import fitz  # PyMuPDF
    except Exception:
        return None

    try:
        file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.page_count == 0:
            return None
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes
    except Exception:
        return None


def png_bytes_to_base64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("utf-8")


def base64_to_png_bytes(value: str) -> bytes:
    return base64.b64decode(value.encode("utf-8"))


def extract_skills_from_text(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        pattern = re.compile(r"\b" + re.escape(skill.lower()) + r"\b", re.IGNORECASE)
        if pattern.search(text_lower):
            found.append(skill)
    return found


def extract_experience_years(text: str) -> int:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+in\s+",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0


def extract_name_from_text(text: str) -> str:
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) < 50 and not any(c.isdigit() for c in line):
            if "@" not in line and "http" not in line.lower():
                return line
    return ""


def extract_email_from_text(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0) if match else ""


def extract_phone_from_text(text: str) -> str:
    match = re.search(r"[\+]?[\d\s\-\(\)]{10,15}", text)
    return match.group(0).strip() if match else ""
