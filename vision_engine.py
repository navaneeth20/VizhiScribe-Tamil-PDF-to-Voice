import io
from PIL import Image

def describe_diagram_in_tamil(pil_image: Image.Image, api_key: str = None, provider: str = "gemini") -> str:
    """
    Generates a concise Tamil explanation of a visual diagram, chart, or book figure for visually impaired students.
    
    :param pil_image: Image object of the diagram/chart
    :param api_key: Optional Gemini or OpenAI API Key
    :param provider: 'gemini' or 'openai'
    :return: Tamil description of the diagram
    """
    if not api_key or not api_key.strip():
        return "[வரைபட விளக்கம்] AI API சாவி வழங்கப்படவில்லை. (படத்தில் உள்ள வரைபடங்கள், அட்டவணைகள் மற்றும் விளக்கப் படங்களை தமிழில் விவரிக்க Gemini/OpenAI API சாவியை உள்ளிடவும்)."

    try:
        if provider.lower() == "gemini":
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            prompt = (
                "You are an expert accessibility scribe assistant for visually impaired Tamil-speaking students. "
                "Analyze this educational diagram/figure/chart and provide a clear, easy-to-understand visual description IN TAMIL. "
                "Describe what key elements are depicted, labeled parts, shapes, and what the student needs to understand from it. "
                "Keep your explanation natural and directly in Tamil script."
            )
            
            # Save PIL image to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type='image/png'),
                    prompt
                ]
            )
            return response.text.strip()
            
        elif provider.lower() == "openai":
            import openai
            import base64
            
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this educational diagram/figure and describe it clearly IN TAMIL for a visually impaired student."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[AI வரைபட பிழை] வரைபடத்தை விவரிப்பதில் சிக்கல் ஏற்பட்டது: {str(e)}"
