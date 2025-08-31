import streamlit as st

def set_base_config(title: str, icon: str = "📄"):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")

def apply_css(path: str = "styles.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
