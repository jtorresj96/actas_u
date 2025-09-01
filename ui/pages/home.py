import os, streamlit as st
import multiprocessing
from ui.components import get_current_user
from ui.layout import apply_css
from upload_files import process_audio, process_pdf, process_txt
from core import db

# ---------- Worker para audio: lee desde archivo en disco ----------
def _audio_worker(uploaded_file: str, doc_id: int, email: str):
    try:
        save_path = os.path.join("uploads", uploaded_file)
        print(save_path)
        with open(save_path, "rb") as fh:
            # adapta si tu firma es distinta (p.ej., process_audio(fh) sin doc_id)
            print(fh)
            process_audio(fh.name, doc_id, email)
    except Exception as e:
        st.error("Error al procesar el archivo de audio.",e)
        db.update_document_status(doc_id, "error", error_message=str(e))

# ---------- Helpers de estado ----------
def _init_state():
    st.session_state.setdefault("confirm_selected", False)
    st.session_state.setdefault("uploader_nonce", 0)
    st.session_state.setdefault("bg_notice", None)  # ← notificación persistente

def _reset_uploader():
    st.session_state["confirm_selected"] = False
    st.session_state["uploader_nonce"] += 1
    st.rerun()

def _close_notice():
    st.session_state["bg_notice"] = None

def _render_notice():
    note = st.session_state.get("bg_notice")
    if note:
        with st.container():
            st.success(
                f"🔊 {note['msg']} — Doc #{note['doc_id']} · {note['filename']}",
                icon="✅",
            )
            if st.button("Cerrar notificación", key="btn_close_notice"):
                _close_notice()
                st.rerun()  # ← fuera del callback, sí funciona


def render() -> None:
    user = get_current_user()
    if not user:
        st.stop()  # vuelve al login si no hay sesión

    apply_css("styles.css")
    _init_state()
    _render_notice()  # ← muestra la tarjeta si existe


    st.markdown('<div class="title">Procesa tus documentos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Sube tus archivos de forma rápida y segura.</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="upload-box">Arrastra y suelta tus archivos aquí</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Subir archivo",
            type=['mp3', 'wav', 'pdf', 'txt'],
            label_visibility="collapsed",
            key=f"uploader_{st.session_state['uploader_nonce']}",  # <-- clave con nonce
        )

    # Barra de uso (demo)
    usados, total = 500, 1500
    restante = total - usados
    porcentaje = int((usados/total) * 100)
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

    # ---------- Confirmación antes de procesar ----------
    if uploaded_file is not None and not st.session_state["confirm_selected"]:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        size_bytes = uploaded_file.size or 0
        size_kb = size_bytes / 1024

        st.warning(
            f"¿Seguro que quieres procesar **{uploaded_file.name}** "
            f"({size_kb:.1f} KB, tipo {file_extension})?",
            icon="⚠️"
        )
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button(
                "Sí, procesar",
                type="primary",
                use_container_width=True,
                key=f"btn_confirm_{st.session_state['uploader_nonce']}",
            ):
                st.session_state["confirm_selected"] = True
                st.rerun()
        with col_cancel:
            if st.button(
                "Cancelar",
                use_container_width=True,
                key=f"btn_cancel_{st.session_state['uploader_nonce']}",
            ):
                _reset_uploader()

    # ---------- Procesamiento ----------
    if uploaded_file is not None and st.session_state["confirm_selected"]:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        size_bytes = uploaded_file.size or 0

        # Guardar archivo original
        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Registrar en BD (status: procesando)
        doc_id = db.insert_document(
            user_id=st.session_state["user_id"],
            filename=uploaded_file.name,
            ext=file_extension.lstrip('.'),
            size_bytes=size_bytes,
            storage_path=save_path
        )

        # Si quieres renombrar con doc_id:
        # new_path = os.path.join("uploads", f"{st.session_state['user_id']}_{doc_id}_{uploaded_file.name}")
        # os.rename(save_path, new_path)
        # save_path = new_path
        # db.update_document_storage_path(doc_id, save_path)

        if file_extension in [".mp3", ".wav"]:
            st.info("Procesando archivo de audio…")
            # Lanza proceso en segundo plano
            email = st.session_state["user_email"]
            p = multiprocessing.Process(target=_audio_worker, args=(uploaded_file.name, doc_id, email))
            p.start()

            # Toast + tarjeta persistente
            st.toast("Proceso de audio iniciado en segundo plano", icon="✅")
            st.success("Proceso de audio iniciado en segundo plano.")  # opcional
            st.session_state["bg_notice"] = {
                "msg": "Proceso de audio iniciado en segundo plano",
                "doc_id": doc_id,
                "filename": uploaded_file.name,
            }
            print("Proceso de audio iniciado en segundo plano")


        elif file_extension == ".pdf":
            st.info("Extrayendo texto del PDF…")
            with st.spinner("Leyendo PDF…"):
                texto = process_pdf(uploaded_file)
            st.subheader("Texto extraído:")
            st.write(texto)
            # (opcional) guardar salida y marcar completado en BD

        elif file_extension == ".txt":
            st.info("Leyendo archivo de texto…")
            with st.spinner("Leyendo .txt…"):
                contenido = process_txt(uploaded_file)
            st.subheader("Contenido del archivo:")
            st.write(contenido)
            # (opcional) guardar salida y marcar completado en BD

        else:
            db.update_document_status(doc_id, "error", error_message="Tipo de archivo no soportado.")
            st.error("Tipo de archivo no soportado.")

        # Reset elegante del uploader y confirmación (evita el error)
        _reset_uploader()
