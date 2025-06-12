import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.title("🧪 JS Eval Test")

html = """
<button onclick="streamlit.setComponentValue('hello')">Click me</button>
"""

selected = streamlit_js_eval(js_expressions=None, html=html, key="simple_test")

if selected:
    st.success(f"JS says: {selected}")