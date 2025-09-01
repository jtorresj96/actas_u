# pages/admin_analytics.py
import os, html
import streamlit as st
import pandas as pd
from datetime import datetime
from core import db
from ui.layout import apply_css  # tu helper de estilos
from typing import Optional

SESSION_KEY = "auth_user"

def _require_admin():
    user = st.session_state.get(SESSION_KEY)
    if not user:
        st.error("Debes iniciar sesión.")
        st.stop()
    if user.get("role") != "admin":
        st.error("No tienes permisos para ver esta página.")
        st.stop()
    return user

def _fmt_ts(seconds: Optional[float]) -> str:
    if seconds is None:
        return "00:00:00.000"
    total = int(seconds)
    ms = int(round((seconds - total) * 1000))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

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
    _require_admin()
    apply_css("styles.css")
    section_html("Analítica (Admin)", "Actividad y archivos de todos los usuarios.", css_class="header")

    # --------- Filtros globales ----------
    fc1, fc2, fc3 = st.columns([1.2, 1.2, 1.2])
    with fc1:
        date_from = st.date_input("Desde", value=None, format="YYYY-MM-DD")
        date_from_str = date_from.isoformat() if date_from else None
    with fc2:
        date_to = st.date_input("Hasta", value=None, format="YYYY-MM-DD")
        date_to_str = date_to.isoformat() if date_to else None
    with fc3:
        status = st.selectbox("Estado", ["Todos", "completado", "procesando", "pendiente", "error"])

    # --------- KPIs + Gráficas ----------
    # --------- KPIs + Gráficas ----------
    stats = db.stats_documents_by_user(date_from_str, date_to_str, status)
    df_stats = pd.DataFrame(stats) if stats else pd.DataFrame(columns=["email","doc_count","total_duration"])

    # ✅ NUEVO: filtro de usuario(s) SOLO para gráficas/KPIs
    all_users = []
    if not df_stats.empty:
        all_users = sorted([u for u in df_stats["email"].fillna("").unique() if u])

    selected_users = st.multiselect(
        "Filtrar usuario(s) para las gráficas",
        options=all_users,
        placeholder="Selecciona uno o varios",
        help="Este filtro afecta los KPIs y las gráficas. (Abajo puedes aplicar el mismo filtro a la tabla)."
    )

    if selected_users:
        df_stats = df_stats[df_stats["email"].isin(selected_users)]

    # Recalcular KPIs con df_stats ya filtrado (si aplica)
    k1, k2, k3 = st.columns(3)
    total_docs = int(df_stats["doc_count"].sum()) if not df_stats.empty else 0
    total_duration = int(df_stats["total_duration"].sum()) if not df_stats.empty else 0
    usuarios_activos = df_stats.shape[0]
    k1.metric("Documentos totales", f"{total_docs:,}")
    k2.metric("Duracion total", _fmt_ts(total_duration/1000.0))
    k3.metric("Usuarios activos", f"{usuarios_activos}")

    gc1, gc2 = st.columns(2)
    with gc1:
        st.subheader("Docs por usuario")
        if df_stats.empty:
            st.caption("Sin datos para el rango seleccionado.")
        else:
            chart_df = df_stats.sort_values("doc_count", ascending=False)[["email","doc_count"]].set_index("email")
            st.bar_chart(chart_df, use_container_width=True)

    with gc2:
        st.subheader("Duracion archivos subidos por usuario")
        if df_stats.empty:
            st.caption("Sin datos para el rango seleccionado.")
        else:
            tmp = df_stats[["email","total_duration"]].copy()
            tmp["Minutos"] = tmp["total_duration"] // (1000*60)
            chart_df2 = tmp.sort_values("total_duration", ascending=False)[["email","Minutos"]].set_index("email")
            st.bar_chart(chart_df2, use_container_width=True)

    st.divider()


    # --------- Tabla detallada (como Historial, pero global) ----------
    st.subheader("Todos los archivos")

    # filtros específicos de tabla
    tc1, tc2, tc3, tc4 = st.columns([2, 1.2, 1.2, 1.4])
    with tc1:
        search = st.text_input("Nombre de archivo", placeholder="Ej: contrato.pdf", key="adm_search")
    with tc2:
        user_query = st.text_input("Usuario (email/nombre)", placeholder="Ej: juan@", key="adm_user_q")
    with tc3:
        order = st.selectbox("Ordenar por", ["Fecha ↓", "Fecha ↑", "Nombre A→Z", "Nombre Z→A", "Usuario A→Z", "Usuario Z→A"], key="adm_order")
    with tc4:
        if st.button("Aplicar filtros", type="primary", key="adm_apply"):
            st.session_state["_apply_admin_filters"] = True

    order_sql = {
        "Fecha ↓": "d.uploaded_at DESC",
        "Fecha ↑": "d.uploaded_at ASC",
        "Nombre A→Z": "d.original_filename ASC",
        "Nombre Z→A": "d.original_filename DESC",
        "Usuario A→Z": "u.email ASC",
        "Usuario Z→A": "u.email DESC",
    }[order]

    if st.session_state.get("_apply_admin_filters", True):
        rows = db.list_all_documents(
            search=search or None,
            status=status,
            date_from=date_from_str,
            date_to=date_to_str,
            user_query=user_query or None,
            order_by=order_sql
        )
        st.session_state["_admin_last_rows"] = rows
        st.session_state["_apply_admin_filters"] = False
    else:
        rows = st.session_state.get("_admin_last_rows", [])

    if not rows:
        st.info("No hay registros.")
        return

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    widths = [0.7, 2.6, 1.5, 1.2, 1.1, 1.6, 1.8, 2.2]  # ID, Archivo, Fecha, Tamaño, Estado, Subido, Resultado, Usuario
    header = st.columns(widths)
    header[0].markdown("**ID**")
    header[1].markdown("**NOMBRE ARCHIVO**")
    header[2].markdown("**FECHA**")
    header[3].markdown("**DURACION**")
    header[4].markdown("**ESTADO**")
    header[5].markdown("**DESCARGAR SUBIDO**")
    header[6].markdown("**DESCARGAR RESULTADO**")
    header[7].markdown("**USUARIO**")

    for r in rows:
        c = st.columns(widths)
        c[0].write(f"#{r['id']}")
        c[1].write(r["original_filename"])

        try:
            dt = datetime.fromisoformat((r["uploaded_at"] or "").replace("Z", ""))
            c[2].write(dt.strftime("%Y-%m-%d %H:%M"))
        except Exception:
            c[2].write(r.get("uploaded_at", ""))

        c[3].write(_fmt_ts(r.get("duration")/1000.0))

        dots = {"completado": "🟢", "procesando": "🟡", "error": "🔴", "pendiente": "⚪"}
        state = r.get("status", "pendiente")
        c[4].write(f"{dots.get(state, '⚪')} {state.capitalize()}")

        # Descargar subido
        storage_path = r.get("storage_path")
        if storage_path and os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                data = f.read()
            c[5].download_button("Descargar", data=data,
                                 file_name=os.path.basename(storage_path),
                                 key=f"adm_dl_orig_{r['id']}", use_container_width=True)
        else:
            c[5].download_button("No disponible", data=b"", disabled=True,
                                 key=f"adm_dl_orig_na_{r['id']}", use_container_width=True)

        # Descargar resultado
        output_path = r.get("output_path")
        if output_path and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                out_bytes = f.read()
            c[6].download_button("Descargar", data=out_bytes,
                                 file_name=os.path.basename(output_path),
                                 key=f"adm_dl_out_{r['id']}", use_container_width=True)
        else:
            c[6].download_button("No disponible", data=b"", disabled=True,
                                 key=f"adm_dl_out_na_{r['id']}", use_container_width=True)

        # Usuario
        user_label = r["email"] or r.get("name", "")
        c[7].write(user_label)

        st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)
