import streamlit as st
from core.auth import authenticate

SESSION_KEY = "auth_user"

def get_current_user():
    return st.session_state.get(SESSION_KEY)

def login_form():
    st.subheader("Iniciar sesión")
    u = st.text_input("Usuario", key="login_user")
    p = st.text_input("Contraseña", type="password", key="login_pass")
    if st.button("Entrar", type="primary"):
        ok, result = authenticate(u, p)
        if ok:
            st.session_state[SESSION_KEY] = result
            st.success("Autenticado.")
            if "id" in result:
                st.session_state["role"] = result["role"]
                st.session_state["user_id"] = result["id"]
                st.session_state["user_email"] = result["email"]

            st.rerun()
        else:
            st.error(result)

def logout_button():
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.pop(SESSION_KEY, None)
        st.rerun()

def require_role(role: str):
    user = get_current_user()
    if not user:
        st.stop()
    if role == "admin" and user["role"] != "admin":
        st.error("No tienes permisos para ver esta página.")
        st.stop()