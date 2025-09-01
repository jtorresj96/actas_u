
from pdf_extractor import extract_text_pdf
import os
from openai_transcription import transcribe_to_docx, TranscriptionConfig


def process_audio(file,id):
    """Procesa un archivo de audio usando la función de transcripción de OpenAI."""
    os.environ["OPENAI_API_KEY"] = ""  # o config.openai_api_key

    cfg = TranscriptionConfig(
        chunk_minutes=10,
        overlap_seconds=2,
        amplify_db=6,
        force_language="es",           # None para autodetect
        export_mp3=True,               # para evitar 413
        model="whisper-1",             # cambia si usas otro
        include_timestamps=False,      # salida sin timestamps
    )

    out_path, blocks, duration = transcribe_to_docx(
        audio_file = os.path.join("uploads", file.name),
        output_docx=f"outputs/{id}_transcripcion.docx",
        config=cfg,
    )

    print("DOCX:", out_path, "Bloques:", blocks)
    return out_path, duration


def process_pdf(file):
    """Procesa un archivo PDF extrayendo su texto."""
    return extract_text_pdf(file)


def process_txt(file):
    """Procesa un archivo de texto decodificándolo a UTF-8."""
    return file.read().decode('utf-8')





