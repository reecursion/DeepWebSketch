import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os

st.set_page_config(layout="wide")

st.title("🖌️ Sketch2Web")

# ---- Layout Columns ----
col1, col2 = st.columns([2, 1])  

# ---- LEFT COLUMN (Whiteboard & Upload) ----
with col1:
    st.subheader("🎨 Draw Your UI or Upload a Sketch")

    # Placeholder for a whiteboard
    whiteboard = st.empty()
    
    # Upload Image
    uploaded_file = st.file_uploader("📂 Upload Sketch (JPG, PNG)", type=["jpg", "png"])
    
    # Display Uploaded Image
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📷 Uploaded Sketch", use_column_width=True)

    # Extra Text Input
    user_input = st.text_area("📝 Additional Instructions", placeholder="E.g., 'Make the button blue'")

# ---- RIGHT COLUMN (LLM Output & Preview) ----
with col2:
    st.subheader("💡 AI-Generated Code")

    # Tabs for HTML and CSS
    tab1, tab2 = st.tabs(["HTML", "CSS"])

    with tab1:
        html_code = st.text_area("📜 HTML Code", placeholder="<div>Hello, World!</div>", height=250)

    with tab2:
        css_code = st.text_area("🎨 CSS Code", placeholder="body { background-color: white; }", height=250)


st.subheader("🌐 Live Preview (Full Width)")

# Combine HTML & CSS for preview
full_code = f"""
<html>
<head>
<style>
{css_code}
</style>
</head>
<body>
{html_code}
</body>
</html>
"""

# Create a temporary file to store generated code
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
    temp_file.write(full_code.encode("utf-8"))
    temp_file_path = temp_file.name

# Display the generated website using an iframe (now full-width)
components.iframe(f"file://{temp_file_path}", height=500, scrolling=True)