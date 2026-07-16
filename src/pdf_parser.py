import fitz  # PyMuPDF


def extract_text(pdf_source):
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
        doc.close()

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

    return text
