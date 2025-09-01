import os, html
from typing import Optional
import streamlit as st
from datetime import datetime
from ui.layout import apply_css
from core import db  # <-- nuestro módulo de BD

def local_css(file_name: str):
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def section_html(title: str, subtitle: str = "", css_class: str = "section"):
    st.markdown(
        f"""
        <div class="{css_class}">
            <h1 class="{css_class}__title">{html.escape(title)}</h1>
            {f'<p class="{css_class}__subtitle">{html.escape(subtitle)}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def render() -> None:
    apply_css("styles.css")
    section_html("Historial de Solicitudes", "Solo verás tus propios documentos.", css_class="header")

    # --- Barra de filtros (estilo inspirado en tu mock) ---
    c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1])
    with c1:
        search = st.text_input("Nombre de archivo", placeholder="Ej: contrato.pdf")
    with c2:
        date_from = st.date_input("Desde", value=None, format="YYYY-MM-DD")
        date_from_str = date_from.isoformat() if date_from else None
    with c3:
        date_to = st.date_input("Hasta", value=None, format="YYYY-MM-DD")
        date_to_str = date_to.isoformat() if date_to else None
    with c4:
        status = st.selectbox("Estado", ["Todos", "completado", "procesando", "pendiente", "error"])

    oc = st.selectbox("Ordenar por", ["Fecha (reciente primero)", "Fecha (antiguo primero)", "Nombre A→Z", "Nombre Z→A"])
    order_sql = {
        "Fecha (reciente primero)": "uploaded_at DESC",
        "Fecha (antiguo primero)": "uploaded_at ASC",
        "Nombre A→Z": "original_filename ASC",
        "Nombre Z→A": "original_filename DESC",
    }[oc]

    if st.button("Aplicar Filtros", type="primary"):
        st.session_state["_apply_filters"] = True

    # cargar datos (aplica filtros si se clickeó o si es la 1ra vez)
    if st.session_state.get("_apply_filters", True):
        rows = db.list_documents_by_user(
            user_id=st.session_state["user_id"],
            search=search or None,
            status=status,
            date_from=date_from_str,
            date_to=date_to_str,
            order_by=order_sql
        )
        st.session_state["_last_rows"] = rows
        st.session_state["_apply_filters"] = False
    else:
        rows = st.session_state.get("_last_rows", [])

    # --- Tabla ---
    if not rows:
        st.info("No hay registros que coincidan con el filtro.")
        return

    # Render tabla estilo “ID / Nombre / Fecha / Tamaño / Estado / Acciones”
    def _fmt_ts(seconds: Optional[float]) -> str:
        if seconds is None:
            return "00:00:00.000"
        total = int(seconds)
        ms = int(round((seconds - total) * 1000))
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    widths = [0.8, 3.6, 1.6, 1.2, 1.2, 1.6, 1.8]   # ajusta a gusto
    header = st.columns(widths)
    header[0].markdown("**ID**")
    header[1].markdown("**NOMBRE ARCHIVO**")
    header[2].markdown("**FECHA**")
    header[3].markdown("**DURACION**")
    header[4].markdown("**ESTADO**")
    header[5].markdown("**DESCARGAR SUBIDO**")
    header[6].markdown("**DESCARGAR RESULTADO**")

    for r in rows:
        print(r)
        c = st.columns(widths)
        c[0].write(f"#{r['id']}")
        c[1].write(r["original_filename"])
        # Fecha local
        try:
            dt = datetime.fromisoformat(r["uploaded_at"].replace("Z", ""))
            c[2].write(dt.strftime("%Y-%m-%d %H:%M"))
        except Exception:
            c[2].write(r["uploaded_at"])
        c[3].write(_fmt_ts(r["duration"] / 1000.0 if r["duration"] is not None else 0))
        # Estado con puntico (simple)
        state = r["status"]
        dots = {"completado": "🟢", "procesando": "🟡", "error": "🔴", "pendiente": "⚪"}
        c[4].write(f"{dots.get(state, '⚪')} {state.capitalize()}")
        # ---- Botón: Descargar archivo subido
        storage_path = r.get("storage_path")
        if storage_path and os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                data = f.read()
            c[5].download_button(
                "Descargar",
                data=data,
                file_name=os.path.basename(storage_path),
                key=f"dl_orig_{r['id']}",
                use_container_width=True
            )
        else:
            c[5].download_button("No disponible", data=b"", disabled=True, key=f"dl_orig_{r['id']}_na", use_container_width=True)

        # ---- Botón: Descargar archivo resultado
        output_path = r.get("output_path")
        if output_path and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                out_bytes = f.read()
            c[6].download_button(
                "Descargar",
                data=out_bytes,
                file_name=os.path.basename(output_path),
                key=f"dl_out_{r['id']}",
                use_container_width=True
            )
        else:
            c[6].download_button("No disponible", data=b"", disabled=True, key=f"dl_out_{r['id']}_na", use_container_width=True)

        st.markdown("---")

    st.markdown('</div>', unsafe_allow_html=True)