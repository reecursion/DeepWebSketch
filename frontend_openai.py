import base64

import base64
import io
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os
from dotenv import load_dotenv
from streamlit_drawable_canvas import st_canvas
from huggingface_hub import InferenceClient
import cv2
from streamlit_ace import st_ace
import re
import io
import os
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
from streamlit_drawable_canvas import st_canvas
from huggingface_hub import InferenceClient
from openai import OpenAI
import openai


# Load environment variables
load_dotenv()

# Set up Streamlit page configuration
st.set_page_config(layout="wide")
st.title("🖌️ Sketch2Web")

# Function to optimize images for processing
def optimize_image(image, max_size=(512, 512), quality=60):
    """Optimize image by resizing and compressing it."""
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    img_width, img_height = image.size
    ratio = min(max_size[0] / img_width, max_size[1] / img_height)
    new_size = (int(img_width * ratio), int(img_height * ratio))
    image = image.resize(new_size, Image.LANCZOS)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr

# Layout for Streamlit interface
col0, col1, col2 = st.columns([1, 3, 2], gap="medium")

with col0:
    st.subheader("Brush Settings")
    drawing_mode = st.selectbox(
        "Drawing Tool:",
        ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
    )
    stroke_width = st.slider("Stroke Width: ", 1, 25, 3)
    stroke_color = st.color_picker("Stroke Color Hex: ")
    realtime_update = st.checkbox("Update in Realtime", True)

    # API selection
    api_choice = st.selectbox("API Choice", ["Hugging Face", "OpenAI"])

with col1:
    st.subheader("🎨 Draw Your UI or Upload a Sketch")
    whiteboard = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="rgba(255, 255, 255, 1)",
        update_streamlit=realtime_update,
        height=400,
        drawing_mode=drawing_mode,
        key="full_app",
    )

    uploaded_file = st.file_uploader("📂 Upload Sketch (JPG, PNG)", type=["jpg", "png"])
    if uploaded_file:
        uploaded_image = Image.open(uploaded_file)
        st.image(uploaded_image, caption="📷 Uploaded Sketch", use_column_width=True)

    user_input = st.text_area("📝 Additional Instructions", placeholder="E.g., 'Make the button blue'")

# Generate Code Button Logic
if st.button("💡 Generate Code"):
    with st.spinner("Generating code..."):
        HF_API_KEY = os.getenv("HF_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if api_choice == "Hugging Face":
            if not HF_API_KEY:
                st.error("Error: Hugging Face API key not found! Set HF_API_KEY in your environment.")
                st.stop()
            client = InferenceClient(api_key=HF_API_KEY)
            model_name = "meta-llama/Llama-3.2-11B-Vision-Instruct"
        elif api_choice == "OpenAI":
            if not OPENAI_API_KEY:
                st.error("Error: OpenAI API key not found! Set OPENAI_API_KEY in your environment.")
                st.stop()
            
            open_api_key = OPENAI_API_KEY
            openai.api_key = open_api_key
            client = OpenAI()
            
        # Prepare image input for the selected API
        image_prompt = ""
        if whiteboard.image_data is not None:
            temp_img_path = "temp_sketch.jpg"
            cv2.imwrite(temp_img_path, whiteboard.image_data)
            with open(temp_img_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode()
            os.remove(temp_img_path)
            image_prompt = f"![Canvas Sketch](data:image/jpeg;base64,{base64_image})\n\n"
        elif uploaded_file:
            optimized_img_bytes = optimize_image(uploaded_image)
            base64_image = base64.b64encode(optimized_img_bytes.getvalue()).decode()
            image_prompt = f"![Uploaded Sketch](data:image/jpeg;base64,{base64_image})\n\n"

        # Generate code using the selected API
        try:
            if api_choice == "Hugging Face":
                messages = [{"role": "user", "content": f"{image_prompt}{user_input}"}]
                completion = client.chat.completions.create(
                    model="meta-llama/Llama-3.2-11B-Vision-Instruct",
                    messages=messages,
                    max_tokens=500
                )
                generated_text = completion.choices[0].message["content"]
            elif api_choice == "OpenAI":
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_input},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ]
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=1000,
                )
                generated_text = response.choices[0].message.content

            # Display generated HTML and CSS code
            html_pattern = r"\`\`\`html\s*(.*?)\`\`\`"
            css_pattern = r"\`\`\`css\s*(.*?)\`\`\`"
            html_code_match = re.search(html_pattern, generated_text, re.DOTALL)
            css_code_match = re.search(css_pattern, generated_text, re.DOTALL)
            # html_code_match = re.search(r"``````", generated_text, re.DOTALL)
            # css_code_match = re.search(r"``````", generated_text, re.DOTALL)

            html_code = html_code_match.group(1).strip() if html_code_match else ""
            css_code = css_code_match.group(1).strip() if css_code_match else ""

            st.session_state["html_code"] = html_code
            st.session_state["css_code"] = css_code

        except Exception as e:
            st.error(f"Error: {str(e)}")

with col2:
    st.subheader("💡 AI-Generated Code")
    tab1, tab2 = st.tabs(["HTML", "CSS"])
    with tab1:
        html_code_displayed = st.text_area(
            label="📜 HTML Code",
            value=st.session_state.get("html_code", ""),
            height=500,
        )
    with tab2:
        css_code_displayed = st.text_area(
            label="🎨 CSS Code",
            value=st.session_state.get("css_code", ""),
            height=500,
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
