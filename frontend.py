import base64
import io
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os
from streamlit_drawable_canvas import st_canvas
from huggingface_hub import InferenceClient

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

            # Process canvas image if available
            image_prompt = ""
            if whiteboard.image_data is not None:
                # Convert numpy array to PIL Image and optimize
                pil_image = Image.fromarray(whiteboard.image_data)
                optimized_img_bytes = optimize_image(pil_image)
                img_base64 = base64.b64encode(optimized_img_bytes.getvalue()).decode()
                image_prompt = f"![Canvas Sketch](data:image/jpeg;base64,{img_base64})\n\n"
                
                
                img_bytes = base64.b64decode(img_base64)

                # Create PIL Image from bytes
                img = Image.open(io.BytesIO(img_bytes))

                # Save as PNG
                img.save('output_image.png', 'PNG')

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
                    "content": f"{image_prompt} Generate HTML and CSS based on this sketch and user request: {user_input}. Give output in the format of [HTML]: <html code> [CSS]: <css code>"
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
            placeholder="""<!DOCTYPE html>
<html>
<head>
    <title>Hello World</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <h1 class="hello-world">Hello World</h1>
</body>
</html>""", 
            height=250
        )

    with tab2:
        css_code = st.text_area(
            "🎨 CSS Code", 
            value=st.session_state.get("css_code", ""), 
            height=250,
            placeholder=""".hello-world {
    color: blue;
    font-size: 36px;
    text-align: center;
}"""
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

full_code = """<!DOCTYPE html>
<html>
<head>
    <title>Hello World</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <h1 class="hello-world">Hello World</h1>
</body>
</html>"""


print(full_code)

# Create a temporary file to store generated code
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
    temp_file.write(full_code.encode("utf-8"))
    temp_file_path = temp_file.name

# Display the generated website using an iframe (now full-width)
components.iframe(f"file://{temp_file_path}", height=500, scrolling=True)
# components.iframe(f"https://www.google.com/", height=500, scrolling=True)
