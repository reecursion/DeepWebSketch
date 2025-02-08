import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os
from streamlit_drawable_canvas import st_canvas
from huggingface_hub import InferenceClient

st.set_page_config(layout="wide")

st.title("🖌️ Sketch2Web")

# ---- Layout Columns ----
col1, col2 = st.columns([2, 1])  

# ---- LEFT COLUMN (Whiteboard & Upload) ----
with col1:
    st.subheader("🎨 Draw Your UI or Upload a Sketch")

    drawing_mode = st.sidebar.selectbox(
        "Drawing tool:",
        ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
    )
    stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
    if drawing_mode == "point":
        point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
    stroke_color = st.sidebar.color_picker("Stroke color hex: ")
    realtime_update = st.sidebar.checkbox("Update in realtime", True)

    # Placeholder for a whiteboard
    whiteboard = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="rgba(255, 255, 255, 1)",
        update_streamlit=realtime_update,
        height=400,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=st.sidebar.checkbox("Display toolbar", True),
        key="full_app",
    )
    
    # Upload Image
    uploaded_file = st.file_uploader("📂 Upload Sketch (JPG, PNG)", type=["jpg", "png"])
    
    # Display Uploaded Image
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📷 Uploaded Sketch", use_column_width=True)

    # Extra Text Input
    user_input = st.text_area("📝 Additional Instructions", placeholder="E.g., 'Make the button blue'")

    if st.button("💡 Generate Code"):
        with st.spinner("Generating code..."):
            # Load API key from environment variable
            HF_API_KEY = os.getenv("HF_API_KEY")

            if not HF_API_KEY:
                st.error("Error: Hugging Face API key not found! Set HF_API_KEY in your environment.")
                st.stop()

            # Initialize Hugging Face Inference Client with Together AI
            client = InferenceClient(
                # provider="together",
                api_key=HF_API_KEY
            )

            # Chat prompt for UI generation
            messages = [
                {
                    "role": "user",
                    "content": f"Generate HTML and CSS based on this user request: {user_input}. Give output in the format of [HTML]: <html code> [CSS]: <css code>"
                }
            ]

            # Request AI-generated code
            try:
                completion = client.chat.completions.create(
                    model="meta-llama/Llama-3.3-70B-Instruct",
                    messages=messages,
                    max_tokens=500
                )

                # Extract generated text
                generated_text = completion.choices[0].message["content"]

                # # Split the generated text into HTML and CSS
                # if "<style>" in generated_text and "</style>" in generated_text:
                #     html_part, css_part = generated_text.split("<style>", 1)
                #     css_part = "<style>" + css_part
                # else:
                #     html_part = generated_text
                #     css_part = ""

                # Store in session state
                st.session_state["html_code"] = generated_text

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ---- RIGHT COLUMN (LLM Output & Preview) ----
with col2:
    st.subheader("💡 AI-Generated Code")

    # Tabs for HTML and CSS
    tab1, tab2 = st.tabs(["HTML", "CSS"])

    with tab1:
        html_code = st.text_area(
            "📜 HTML Code", 
            value=st.session_state.get("html_code", ""), 
            placeholder="""Your HTML Code""", 
            height=250
        )

    with tab2:
        css_code = st.text_area(
            "🎨 CSS Code", 
            value=st.session_state.get("css_code", ""), 
            height=250,
            placeholder="""Your CSS Code"""
        )

st.subheader("🌐 Live Preview (Full Width)")

# # Combine HTML & CSS for preview
# full_code = f"""
# <html>
# <head>
# <style>
# {css_code}
# </style>
# </head>
# <body>
# {html_code}
# </body>
# </html>
# """


# Define a static example before AI-generated code is available
default_html = """
<!DOCTYPE html>
<html>
<head>
<style>
h1 {
    color: black;
    text-align: center;
    font-family: Arial, sans-serif;
}
</style>
</head>
<body>
    <h1>Hello, World!</h1>
</body>
</html>
"""

# Use AI-generated content if available
html_code = st.session_state.get("html_code", "<h1>Hello, World!</h1>")
css_code = st.session_state.get("css_code", "h1 { color: blue; }")

full_code = f"""
<!DOCTYPE html>
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
""" if "html_code" in st.session_state else default_html

# Ensure the temporary file is written correctly
with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
    temp_file.write(full_code)
    temp_file_path = temp_file.name

with open(temp_file_path, "r", encoding="utf-8") as file:
    html_content = file.read()

st.components.v1.html(html_content, height=500, scrolling=True)