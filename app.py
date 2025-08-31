import streamlit as st
import os
from upload_files import process_audio, process_pdf, process_txt

def local_css(file_name):
    with open(file_name, 'r') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    local_css("styles.css")
    

    st.markdown('<div class="title">Procesa tus documentos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Sube tus archivos de forma rápida y segura.</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="upload-box">Arrastra y suelta tus archivos aquí</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Subir archivo",
            type=['mp3', 'wav', 'pdf', 'txt'],
            label_visibility="collapsed"
        )

    archivos_usados = 500
    archivos_totales = 1500
    archivos_restantes = archivos_totales - archivos_usados
    porcentaje = int((archivos_usados / archivos_totales) * 100)

    st.progress(porcentaje)
    st.markdown(
        f"""
        <div class="progress-box">
            <div><b>Archivos usados:</b> {archivos_usados}</div>
            <div><b>Archivos restantes:</b> {archivos_restantes}</div>
        </div>
        <p style="text-align:center; color:#666;">Has usado el {porcentaje}% de tu cuota mensual.</p>
        """,
        unsafe_allow_html=True
    )

    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        if file_extension in ['.mp3', '.wav']:
            st.write('Procesando archivo de audio...')
            result = process_audio(uploaded_file)
            st.subheader('Transcripción:')
            st.write(result)

        elif file_extension == '.pdf':
            st.write('Extrayendo texto del PDF...')
            result = process_pdf(uploaded_file)
            st.subheader('Texto extraído:')
            st.write(result)

        elif file_extension == '.txt':
            st.write('Leyendo archivo de texto...')
            result = process_txt(uploaded_file)
            st.subheader('Contenido del archivo:')
            st.write(result)
        else:
            st.error('Tipo de archivo no soportado.')


if __name__ == '__main__':
    main()
