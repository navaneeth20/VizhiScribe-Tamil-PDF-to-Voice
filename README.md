# VizhiScribe (விழி-ஸ்கிரைப்) 🎙️📖
### Tamil PDF, Image & Diagram to Audio Note Converter for Visually Impaired Students

**VizhiScribe** is a Python application designed for scribes, educators, and visually challenged students to load Tamil textbook PDFs, scanned book pages, and images containing text and complex diagrams, converting them into natural, spoken Tamil audio notes (.mp3).

---

## 🌟 Key Features

1. **📄 Digital PDF & Scanned Page Reader**:
   - Automatically extracts digital text from Tamil PDF books.
   - Includes OCR capabilities (`pytesseract` / `easyocr`) for scanned book pages.

2. **🖼️ AI Diagram & Figure Describer**:
   - Educational books often contain diagrams, flowcharts, or body system figures.
   - Generates natural Tamil visual descriptions of diagrams using Gemini or OpenAI Vision AI, ensuring blind students don't miss visual context.

3. **🗣️ Natural Neural Tamil Text-to-Speech (TTS)**:
   - Powered by Microsoft Edge's Neural Tamil voices (`ta-IN-PallaviNeural`, `ta-IN-ValluvarNeural`, `ta-LK-SaranyaNeural`, etc.).
   - Ultra-natural human pronunciation free of API costs, with fallback to Google Text-to-Speech (`gTTS`).
   - Adjustable speech rate (-40% to +80%) for fast listening.

4. **✏️ Scribe Editing Workspace**:
   - Allows scribes to review, edit OCR output, expand mathematical formulas, or add custom explanatory notes before generating audio notes.

5. **👁️ Low-Vision High Contrast Mode**:
   - Built-in High Contrast Theme (Yellow text on black background with extra large fonts) designed specifically for low-vision students.

6. **📦 Full Chapter Audio Exporter**:
   - Export individual page MP3s or download the full chapter concatenated as a single MP3 audio book or ZIP bundle.

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
Open terminal or command prompt in the project directory and run:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the Streamlit app:
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 📂 Project Structure

- `app.py` - Streamlit Web Application Interface.
- `ocr_engine.py` - PDF parsing, digital text extraction, and Tamil OCR module.
- `tts_engine.py` - High-quality Neural Tamil speech synthesis & audio stitching.
- `vision_engine.py` - AI diagram and image vision describer in Tamil.
- `utils.py` - High contrast styling and ZIP archive export utilities.
- `requirements.txt` - Python package dependencies.
