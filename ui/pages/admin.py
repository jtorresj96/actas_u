import streamlit as st
from ui.components import require_role
from ui.layout import apply_css
from repositories.users import list_users, create_user, update_user_active, reset_password

def render() -> None:
    apply_css("styles.css")
    require_role("admin")
    st.title("Administración de usuarios")

    tabs = st.tabs(["Crear usuario", "Listado y acciones"])

    with tabs[0]:
        st.subheader("Crear usuario")
        new_user = st.text_input("Usuario")
        new_name = st.text_input("Nombre")
        new_email = st.text_input("Email")
        new_pass = st.text_input("Contraseña", type="password")
        role = st.selectbox("Rol", ["user", "admin"])
        active = st.checkbox("Activo", value=True)
        if st.button("Crear", type="primary"):
            if not new_user or not new_pass:
                st.warning("Usuario y contraseña son obligatorios.")
            else:
                try:
                    create_user(new_user, new_pass, new_name, new_email, role=role, active=active)
                    st.success("Usuario creado.")
                except Exception as e:
                    st.error(f"No se pudo crear: {e}")

    with tabs[1]:
        st.subheader("Usuarios")
        users = list_users()
        if not users:
            st.info("No hay usuarios.")
            return

        for u in users:
            c1, c2, c3, c4, c5 = st.columns([2,1,1,1,2])
            with c1:
                st.write(f"**{u['username']}**")
                st.caption(f"Creado: {u['created_at']}")
            with c2:
                st.write(u['role'])
            with c3:
                st.write("Activo" if u['active'] else "Inactivo")
            with c4:
                label = "Desactivar" if u["active"] else "Activar"
                if st.button(label, key=f"toggle_{u['id']}"):
                    ok = update_user_active(u["username"], not u["active"])
                    st.success("Actualizado." if ok else "Sin cambios.")
                    st.experimental_rerun()
            with c5:
                with st.popover("Reset contraseña", use_container_width=True):
                    np = st.text_input("Nueva contraseña", type="password", key=f"np_{u['id']}")
                    if st.button("Aplicar", key=f"apply_{u['id']}"):
                        if not np:
                            st.warning("No puede estar vacía.")
                        else:
                            ok = reset_password(u["username"], np)
                            st.success("Actualizada." if ok else "No se actualizó.")
