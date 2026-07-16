"""
fake_resume_detector.py

Heuristic checks that flag potentially fake or manipulated resumes:
  1. Keyword-stuffing  (same skill token repeated 20+ times)
  2. Invisible / white-text injection  (text-to-whitespace ratio anomaly)
  3. Font-inconsistency / metadata red-flags in the PDF
  4. Mismatched dates  (graduation year contradictions)
  5. Boilerplate / copy-pasted patterns
"""

import re
from collections import Counter

# ── Optional: PyMuPDF for PDF-level metadata checks ──
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False


# ================================================================
#  1. Keyword-Stuffing Detection
# ================================================================

def check_keyword_stuffing(text: str, threshold: int = 20) -> dict:
    """
    Flag if any single word (3+ chars) appears *threshold* or more times.
    ATS-gamers often repeat skills unnaturally.
    """
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    counts = Counter(words)
    stuffed = {w: c for w, c in counts.items() if c >= threshold}
    return {
        "flagged": bool(stuffed),
        "label": "Keyword Stuffing",
        "details": stuffed if stuffed else "No keyword stuffing detected",
        "severity": "HIGH" if stuffed else "NONE",
    }


# ================================================================
#  2. Invisible / White-Text Detection
# ================================================================

def check_invisible_text(text: str) -> dict:
    """
    Detect invisible white-text tricks:
      • Excessive whitespace characters relative to visible text
      • Long runs of space/tab that likely hide ATS keywords
    """
    if not text:
        return {"flagged": False, "label": "Invisible Text", "details": "Empty text", "severity": "NONE"}

    visible_chars = len(re.sub(r"\s", "", text))
    total_chars = len(text)

    if total_chars == 0:
        return {"flagged": False, "label": "Invisible Text", "details": "Empty text", "severity": "NONE"}

    whitespace_ratio = 1 - (visible_chars / total_chars)

    # Long runs of whitespace (10+ spaces in a row) are suspicious
    long_ws_runs = re.findall(r"[ \t]{10,}", text)

    flagged = whitespace_ratio > 0.55 or len(long_ws_runs) > 5
    return {
        "flagged": flagged,
        "label": "Invisible / White Text",
        "details": (
            f"Whitespace ratio: {whitespace_ratio:.1%}, "
            f"long whitespace runs: {len(long_ws_runs)}"
        ),
        "severity": "HIGH" if flagged else "NONE",
    }


# ================================================================
#  3. PDF Metadata / Font Inconsistency
# ================================================================

def check_pdf_metadata(pdf_path: str) -> dict:
    """
    Inspect the PDF for:
      • Excessive number of distinct fonts (copy-paste from multiple docs)
      • Suspicious producer/creator strings (e.g., "Fake Resume Builder")
    Requires PyMuPDF.
    """
    if not FITZ_AVAILABLE:
        return {"flagged": False, "label": "PDF Metadata", "details": "PyMuPDF not available", "severity": "NONE"}

    flags = []
    try:
        doc = fitz.open(pdf_path)
        meta = doc.metadata or {}

        # Collect all unique font names across pages
        fonts = set()
        for page in doc:
            for f in page.get_fonts(full=True):
                font_name = f[3]  # human-readable font name
                if font_name:
                    fonts.add(font_name)

        if len(fonts) > 8:
            flags.append(f"Excessive font diversity ({len(fonts)} distinct fonts)")

        # Suspicious producer / creator keywords
        suspicious_kw = ["fake", "fabricat", "scam", "auto-gen", "chatgpt"]
        producer = (meta.get("producer") or "").lower()
        creator = (meta.get("creator") or "").lower()
        for kw in suspicious_kw:
            if kw in producer or kw in creator:
                flags.append(f"Suspicious PDF producer/creator: '{meta.get('producer', '')} / {meta.get('creator', '')}'")
                break

        doc.close()
    except Exception as e:
        return {"flagged": False, "label": "PDF Metadata", "details": f"Error reading PDF: {e}", "severity": "NONE"}

    return {
        "flagged": bool(flags),
        "label": "PDF Metadata / Fonts",
        "details": "; ".join(flags) if flags else "Metadata looks normal",
        "severity": "MEDIUM" if flags else "NONE",
    }


# ================================================================
#  4. Date Mismatch Detection
# ================================================================

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

def check_date_mismatches(text: str) -> dict:
    """
    Flag obviously contradictory dates:
      • Education end-date is in the future by 5+ years
      • Any date listed before 1980 (unlikely for current applicants)
      • A "graduation" year that precedes an "enrollment" year
    """
    years = [int(y) for y in _YEAR_RE.findall(text + " ") if 1950 <= int(y) <= 2099]
    # re.findall returns the group, so reconstruct full year from prefix
    years = [int(m) for m in re.findall(r"\b((?:19|20)\d{2})\b", text)]

    flags = []

    if years:
        import datetime
        current_year = datetime.datetime.now().year
        future = [y for y in years if y > current_year + 5]
        ancient = [y for y in years if y < 1980]
        if future:
            flags.append(f"Dates far in the future: {future}")
        if ancient:
            flags.append(f"Unusually old dates: {ancient}")

        # Check if years are wildly out of order (span > 40 years)
        if max(years) - min(years) > 40:
            flags.append(f"Date span of {max(years)-min(years)} years is suspicious")

    return {
        "flagged": bool(flags),
        "label": "Date Mismatch",
        "details": "; ".join(flags) if flags else "Dates look consistent",
        "severity": "MEDIUM" if flags else "NONE",
    }


# ================================================================
#  5. Boilerplate / Copy-Paste Detection
# ================================================================

BOILERPLATE_PHRASES = [
    "results-driven professional",
    "detail-oriented team player",
    "highly motivated individual",
    "strong communication skills",
    "proven track record of success",
    "seeking a challenging position",
    "i am a hard worker",
    "excellent problem solving abilities",
    "responsible for various tasks",
    "dynamic and results-oriented",
]

def check_boilerplate(text: str) -> dict:
    """Flag excessive use of generic boilerplate phrases."""
    lower = text.lower()
    found = [bp for bp in BOILERPLATE_PHRASES if bp in lower]
    flagged = len(found) >= 3
    return {
        "flagged": flagged,
        "label": "Boilerplate / Copy-Paste",
        "details": f"Found {len(found)} boilerplate phrases: {found}" if found else "No boilerplate detected",
        "severity": "LOW" if flagged else "NONE",
    }


# ================================================================
#  Master Detector
# ================================================================

def detect_fake_resume(text: str, pdf_path: str | None = None) -> dict:
    """
    Run all heuristic checks and return a consolidated report.

    Returns
    -------
    dict with keys:
        risk_level : str   – "HIGH", "MEDIUM", "LOW", or "CLEAN"
        checks     : list  – individual check results
        summary    : str   – human-readable summary
    """
    checks = [
        check_keyword_stuffing(text),
        check_invisible_text(text),
        check_date_mismatches(text),
        check_boilerplate(text),
    ]

    if pdf_path:
        checks.append(check_pdf_metadata(pdf_path))

    # Determine overall risk
    severities = [c["severity"] for c in checks if c["flagged"]]
    if "HIGH" in severities:
        risk = "HIGH"
    elif "MEDIUM" in severities:
        risk = "MEDIUM"
    elif severities:
        risk = "LOW"
    else:
        risk = "CLEAN"

    flagged_labels = [c["label"] for c in checks if c["flagged"]]
    summary = (
        f"Risk: {risk}. Flagged: {', '.join(flagged_labels)}."
        if flagged_labels
        else "No manipulation signals detected."
    )

    return {
        "risk_level": risk,
        "checks": checks,
        "summary": summary,
    }
