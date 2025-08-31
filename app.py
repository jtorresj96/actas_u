import streamlit as st
import tempfile
import os

# Importar librerías necesarias para extraer texto de PDFs y procesar audio
import PyPDF2
import whisper


def transcribe_audio(file):
    # Guarda el archivo en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name
    # Cargar el modelo de Whisper (puedes cambiar el tamaño, ej. 'small', 'base', 'large')
    model = whisper.load_model('small')
    result = model.transcribe(tmp_path)
    # Elimina el archivo temporal
    os.remove(tmp_path)
    return result.get('text', 'No se pudo transcribir.')


def extract_text_pdf(file):
    reader = PyPDF2.PdfReader(file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() + "\n"
    return extracted_text


def main():
    st.title('Procesador de documentos: Audio, PDF o Texto')
    st.write('Sube un archivo de audio (mp3, wav), PDF o un documento de texto (.txt) y lo procesaremos.')

    uploaded_file = st.file_uploader('Elige un archivo', type=['mp3', 'wav', 'pdf', 'txt'])

    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        if file_extension in ['.mp3', '.wav']:
            st.write('Procesando archivo de audio...')
            transcription = transcribe_audio(uploaded_file)
            st.subheader('Transcripción:')
            st.write(transcription)

        elif file_extension == '.pdf':
            st.write('Extrayendo texto del PDF...')
            text = extract_text_pdf(uploaded_file)
            st.subheader('Texto extraído:')
            st.write(text)

        elif file_extension == '.txt':
            st.write('Leyendo archivo de texto...')
            text = uploaded_file.read().decode('utf-8')
            st.subheader('Contenido del archivo:')
            st.write(text)
        else:
            st.error('Tipo de archivo no soportado.')


if __name__ == '__main__':
    main()
