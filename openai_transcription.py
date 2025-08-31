import tempfile
import os
import openai


def transcribe_audio(file):
    """Transcribe an audio file using OpenAI's Speech-to-Text API."""
    # Obtener la extensión del archivo original
    suffix = os.path.splitext(file.name)[1] if hasattr(file, 'name') else '.mp3'
    
    # Guarda el archivo en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name
    
    # Transcribir usando el modelo "whisper-1"
    with open(tmp_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    
    # Elimina el archivo temporal
    os.remove(tmp_path)
    
    return transcript.get("text", "No se pudo transcribir.")
