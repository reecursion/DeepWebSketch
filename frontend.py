import base64
import io
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os
from streamlit_drawable_canvas import st_canvas
from huggingface_hub import InferenceClient
import cv2
from streamlit_ace import st_ace
import re

st.set_page_config(layout="wide")

st.title("🖌️ Sketch2Web")

def optimize_image(image, max_size=(512, 512), quality=60):
    """
    Optimize image by resizing and compressing it
    """
    # Convert to RGB if image is in RGBA mode
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Calculate aspect ratio-preserving dimensions
    img_width, img_height = image.size
    ratio = min(max_size[0]/img_width, max_size[1]/img_height)
    new_size = (int(img_width*ratio), int(img_height*ratio))
    
    # Resize image using older PIL syntax
    image = image.resize(new_size, Image.LANCZOS)
    
    # Save with compression
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
    img_byte_arr.seek(0)
    
    return img_byte_arr

# ---- Layout Columns ----
col0, col1, col2 = st.columns([1, 3, 2], gap="medium")  

with col0:
    st.subheader("Brush Settings")

    drawing_mode = st.selectbox(
        "Drawing tool:",
        ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
    )
    stroke_width = st.slider("Stroke width: ", 1, 25, 3)
    if drawing_mode == "point":
        point_display_radius = st.slider("Point display radius: ", 1, 25, 3)
    stroke_color = st.color_picker("Stroke color hex: ")
    realtime_update = st.checkbox("Update in realtime", True)


# ---- LEFT COLUMN (Whiteboard & Upload) ----
with col1:
    st.subheader("🎨 Draw Your UI or Upload a Sketch")

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
                api_key=HF_API_KEY
            )

            # Process canvas image if available
            image_prompt = ""
            if whiteboard.image_data is not None:
                cv2.imwrite(f"img.jpg",  whiteboard.image_data)
                image = None 
                with open("img.jpg", "rb") as f:
                    image = base64.b64encode(f.read()).decode("utf-8")
                image_prompt = f"![Canvas Sketch](data:image/jpeg;base64,{image})\n\n"

            # Process uploaded image if available
            elif uploaded_file:
                pil_image = Image.open(uploaded_file)
                optimized_img_bytes = optimize_image(pil_image)
                img_base64 = base64.b64encode(optimized_img_bytes.getvalue()).decode()
                image_prompt = f"![Uploaded Sketch](data:image/jpeg;base64,{img_base64})\n\n"



            # Chat prompt for UI generation
            messages = [
                {
                    "role": "user",
                    "content": f"{image_prompt} Generate HTML and CSS based on this sketch and user request: {user_input}. Provide the code using blocks of triple backticks. Respond with only the code in HTML and CSS, nothing else."
                }
            ]

            # Request AI-generated code
            try:
                completion = client.chat.completions.create(
                    model="meta-llama/Llama-3.2-11B-Vision-Instruct",
                    messages=messages,
                    max_tokens=500
                )

                # Extract generated text
                generated_text = completion.choices[0].message["content"]
                print(generated_text)

                html_pattern = r"\`\`\`html\s*(.*?)\`\`\`"
                css_pattern = r"\`\`\`css\s*(.*?)\`\`\`"

                html_match = re.search(html_pattern, generated_text, re.DOTALL)
                css_match = re.search(css_pattern, generated_text, re.DOTALL)
                
                # Store in session state
                st.session_state["html_code"] = html_match.group(1).strip() if html_match else ""
                st.session_state["css_code"] = css_match.group(1).strip() if css_match else ""
                if not html_match and not css_match:
                    st.warning("Could not parse HTML or CSS from the generated text. Please try again.")

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
            height=500
        )

        # html_code = st_ace(
        #     value=st.session_state.get("html_code", ""),
        #     language="html",
        #     theme="monokai",
        #     key="html_editor",
        #     placeholder="Your HTML Code",
        #     height=500,
        #     font_size=14,
        #     wrap=True,
        #     show_gutter=True,
        #     show_print_margin=False,
        #     annotations=None,
        #     keybinding="vscode",
        #     min_lines=20,
        #     auto_update=True,
        # )

    with tab2:
        css_code = st.text_area(
            "🎨 CSS Code", 
            value=st.session_state.get("css_code", ""), 
            height=500,
            placeholder="""Your CSS Code"""
        )

        # css_code = st_ace(
        #     value=st.session_state.get("css_code", ""),
        #     language="css",
        #     theme="monokai",
        #     key="css_editor",
        #     placeholder="Your CSS Code",
        #     height=500,
        #     font_size=14,
        #     wrap=True,
        #     show_gutter=True,
        #     show_print_margin=False,
        #     annotations=None,
        #     keybinding="vscode",
        #     min_lines=20,
        #     auto_update=True,
        # )

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