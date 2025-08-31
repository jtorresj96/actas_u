from openai_transcription import transcribe_audio
from pdf_extractor import extract_text_pdf


def process_audio(file):
    """Procesa un archivo de audio usando la función de transcripción de OpenAI."""
    return transcribe_audio(file)


def process_pdf(file):
    """Procesa un archivo PDF extrayendo su texto."""
    return extract_text_pdf(file)


def process_txt(file):
    """Procesa un archivo de texto decodificándolo a UTF-8."""
    return file.read().decode('utf-8')
