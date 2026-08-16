import pymupdf  # PyMuPDF
from PIL import Image
import io
import os
import re

def extract_pdf_pages_data(pdf_file_bytes: bytes):
    """
    Parses a PDF file from bytes.
    Returns a list of dicts for each page containing:
    - page_num (1-indexed)
    - text: Extracted digital text (if present)
    - image: PIL Image of the rendered page
    - embedded_images: List of PIL Images embedded within the page (diagrams/charts)
    """
    doc = pymupdf.open(stream=pdf_file_bytes, filetype="pdf")
    pages_data = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        
        # 1. Render page to high-res image for display & vision AI
        pix = page.get_pixmap(dpi=150)
        page_img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # 2. Extract digital text
        digital_text = page.get_text("text").strip()
        
        # 3. Extract embedded diagrams/images
        embedded_images = []
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            try:
                emb_img = Image.open(io.BytesIO(image_bytes))
                # Only include reasonably sized images (skip tiny bullet point icons)
                if emb_img.width > 80 and emb_img.height > 80:
                    embedded_images.append(emb_img)
            except Exception:
                continue

        pages_data.append({
            "page_num": page_idx + 1,
            "text": clean_tamil_text(digital_text),
            "image": page_img,
            "embedded_images": embedded_images,
            "is_scanned": len(digital_text) < 10 # heuristic for scanned page
        })
        
    doc.close()
    return pages_data

_RAPID_OCR = None

def get_rapid_ocr():
    global _RAPID_OCR
    if _RAPID_OCR is None:
        from rapidocr_onnxruntime import RapidOCR
        _RAPID_OCR = RapidOCR()
    return _RAPID_OCR

def perform_ocr_on_image(pil_image: Image.Image, lang: str = "tam+eng", api_key: str = None) -> str:
    """
    Performs OCR on a PIL image.
    Tries RapidOCR/Tesseract first, or Gemini AI Vision if API key is provided.
    """
    # 0. Try Gemini AI Vision if API Key is available (Highest accuracy for Tamil scanned text!)
    if api_key and api_key.strip():
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            prompt = "Extract all Tamil and English text from this scanned image page word-for-word accurately. Return only the extracted text without any preamble."
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[types.Part.from_bytes(data=img_bytes, mime_type='image/png'), prompt]
            )
            extracted = response.text.strip()
            if extracted:
                return clean_tamil_text(extracted)
        except Exception as e:
            print(f"[OCR Vision Error] Gemini OCR failed: {e}")

    # 1. Try RapidOCR (Lightweight ONNX OCR)
    try:
        import numpy as np
        engine = get_rapid_ocr()
        img_np = np.array(pil_image)
        result, _ = engine(img_np)
        if result:
            txt_lines = [line[1] for line in result]
            extracted = "\n".join(txt_lines)
            if extracted.strip():
                return clean_tamil_text(extracted)
    except Exception as e:
        print(f"[OCR Info] RapidOCR error: {e}")

    # 2. Try PyTesseract
    try:
        import pytesseract
        text = pytesseract.image_to_string(pil_image, lang=lang)
        if text.strip():
            return clean_tamil_text(text)
    except Exception as e:
        print(f"[OCR Info] Tesseract error: {e}")

    return "[OCR தகவல்] ஸ்கேன் செய்யப்பட்ட இந்த பக்கத்தில் உரையைப் பிரித்தெடுக்க மெனுவில் உள்ள Gemini API சாவியை உள்ளிடவும் அல்லது உங்கள் உரையை தட்டச்சு செய்யவும்."

def clean_tamil_text(text: str) -> str:
    """
    Cleans OCR output & Tamil text formatting for smoother TTS playback.
    """
    if not text:
        return ""
        
    # Replace multiple spaces / newlines with single space
    cleaned = re.sub(r'[\r\t\f\v]', ' ', text)
    # Fix hyphenated words across lines
    cleaned = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned)
    # Convert excessive newlines to paragraph stops
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # Remove orphan page numbers like "Page 12" or "பக்கம் 5"
    cleaned = re.sub(r'(?i)^(page|பக்கம்)\s*\d+\s*$', '', cleaned, flags=re.MULTILINE)
    
    return cleaned.strip()
