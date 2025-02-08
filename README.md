# DeepWebSketch:  🖌️

DeepWebSketch is an innovative web application that converts hand-drawn sketches into working HTML/CSS code using AI. Draw your UI design or upload a sketch, and watch as it transforms into functional web code in real-time.

Built during the TartanHacks 2025 Hackathon by team WrapperAI! 
Team members: Manav Kapadnis, 

## Features

- **Interactive Canvas**: Draw UI elements using multiple tools:
  - Freehand drawing
  - Lines, rectangles, and circles
  - Polygon and point tools
  - Transform capabilities
  
- **Flexible Input Methods**:
  - Real-time drawing canvas
  - Image upload support (JPG, PNG)
  - Additional text instructions

- **Dual AI Integration**:
  - Hugging Face (Meta-Llama 3.2-11B-Vision-Instruct)
  - OpenAI (GPT-4-Vision)

- **Live Code Generation**:
  - Generates HTML and CSS code
  - Real-time preview
  - Code editing capabilities

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sketch2web.git
cd sketch2web
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add your API keys:
```
HF_API_KEY=your_huggingface_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

3. Choose your preferred drawing tool and settings:
   - Select drawing mode (freedraw, shapes, etc.)
   - Adjust stroke width and color
   - Enable/disable realtime updates

4. Create your UI design:
   - Draw directly on the canvas, or
   - Upload an existing sketch

5. Add any additional instructions in the text area

6. Click "Generate Code" to create HTML/CSS code

7. View and edit the generated code in the HTML and CSS tabs

8. See the live preview of your design

## Dependencies

- streamlit
- streamlit-drawable-canvas
- Pillow
- python-dotenv
- huggingface-hub
- openai
- opencv-python
- streamlit-ace

## Environment Variables

- `HF_API_KEY`: Hugging Face API key for access to the Llama model
- `OPENAI_API_KEY`: OpenAI API key for access to GPT-4-Vision

## Limitations

- Image size is optimized to 512x512 pixels for API processing
- Generated code may require manual refinement
- API response times may vary based on server load

## Acknowledgments

- Streamlit for the web framework
- Hugging Face and OpenAI for AI capabilities
- The open-source community for various dependencies
