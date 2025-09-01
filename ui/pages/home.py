import os, streamlit as st
from ui.components import get_current_user
from ui.layout import apply_css
from upload_files import process_audio, process_pdf, process_txt
from core import db

def render() -> None:
    user = get_current_user()
     # vuelve al login si no hay sesión

    apply_css("styles.css")
    st.markdown('<div class="title">Procesa tus documentos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Sube tus archivos de forma rápida y segura.</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="upload-box">Arrastra y suelta tus archivos aquí</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Subir archivo", type=['mp3','wav','pdf','txt'], label_visibility="collapsed")

    # Ejemplo de cuota: cámbialo cuando agregues tabla de uso por usuario
    usados, total = 500, 1500
    restante = total - usados
    porcentaje = int((usados/total)*100)
    st.progress(porcentaje)
    st.markdown(
        f"""
        <div class="progress-box">
            <div><b>Archivos usados:</b> {usados}</div>
            <div><b>Archivos restantes:</b> {restante}</div>
        </div>
        <p style="text-align:center; color:#666;">Has usado el {porcentaje}% de tu cuota mensual.</p>
        """,
        unsafe_allow_html=True
    )

    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        size_bytes = uploaded_file.size or 0

        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer()) 

        doc_id = db.insert_document(
            user_id=st.session_state["user_id"],
            filename=uploaded_file.name,
            ext=file_extension.lstrip('.'),
            size_bytes=size_bytes,
            storage_path=save_path 
         ) 

        if file_extension in [".mp3", ".wav"]:
            st.info("Procesando archivo de audio…")
            st.subheader("Transcripción:")
            out_path, duration = process_audio(uploaded_file, doc_id)
            st.write(out_path)
        elif file_extension == ".pdf":
            st.info("Extrayendo texto del PDF…")
            st.subheader("Texto extraído:")
            st.write(process_pdf(uploaded_file))
        elif file_extension == ".txt":
            st.info("Leyendo archivo de texto…")
            st.subheader("Contenido del archivo:")
            st.write(process_txt(uploaded_file))
        else:
            st.error("Tipo de archivo no soportado.")


        


        db.update_document_status(doc_id, "completado", out_path, duration)

