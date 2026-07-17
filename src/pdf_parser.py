import fitz  # PyMuPDF


def extract_text(pdf_source):
    """
    Extract visible text from a PDF, plus the URLs behind any hyperlinks
    on the page.

    FIX: many resume templates (Canva/Figma exports especially) link a
    small icon to a GitHub/LinkedIn profile as a PDF link *annotation*,
    with no visible URL text printed anywhere on the page. page.get_text()
    only returns rendered text, so those links were silently invisible to
    every downstream regex (entity_extractor.py's GitHub/LinkedIn/phone
    detection). We now also walk page.get_links() and append any http(s)/
    mailto/tel URIs found, right after that page's text, so they're
    available to the same regex-based extraction.
    """
    text = ""
    try:
        if hasattr(pdf_source, "read"):
            pdf_source.seek(0)
            pdf_bytes = pdf_source.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)

        for page in doc:
            text += page.get_text()
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    text += "\n" + uri
        doc.close()

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

    return text
