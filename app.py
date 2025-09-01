import os
import streamlit as st
from core.db import init_db, seed_admin_if_empty
from ui.components import login_form, get_current_user, logout_button
from ui.layout import set_base_config
from ui.pages import home, admin, historial, admin_analytics

set_base_config(title="Procesa tus documentos", icon="📄")
PAGES_ADMIN = {
    "Cargar documentos": home.render,
    "Historial": historial.render,
    "Admin": admin.render,
    "Analitica": admin_analytics.render,
    
}

PAGES_USER = {
    "Cargar documentos": home.render,
    "Historial": historial.render,
    
}

def main():
    
    init_db()
    seed_admin_if_empty()

    user = get_current_user()
    if not user:
        st.title("Procesa tus documentos")
        login_form()
        return
    
    role = st.session_state["role"]

    st.sidebar.success(f"Conectado como: {user['username']} ({user['role']})")

    # Cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    pages = PAGES_ADMIN if role == "admin" else PAGES_USER
    selection = st.sidebar.selectbox("Menú", options=list(pages))
    pages[selection]()

    st.write("💡 Usa el menú lateral: ve a **Home** para procesar archivos o **Admin** para gestionar usuarios.")

if __name__ == "__main__":
    # Variables opcionales para sembrar admin por primera vez
    os.environ.setdefault("ADMIN_USER", "admin")
    os.environ.setdefault("ADMIN_PASSWORD", "admin123")
    main()
