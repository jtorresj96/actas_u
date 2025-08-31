import PyPDF2


def extract_text_pdf(file):
    """Extracts text from a PDF file using PyPDF2."""
    reader = PyPDF2.PdfReader(file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() + "\n"
    return extracted_text
