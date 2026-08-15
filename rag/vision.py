"""
Stage 2c: IMAGE -> CAPTION (Vision Encoder box in the architecture diagram)

Always API-backed. Image understanding goes through the Gemini Vision API.
"""
import PIL.Image
from . import config


def caption_image(image_path: str) -> str:
    if not config.GOOGLE_API_KEY:
        return "[Image - caption unavailable: GOOGLE_API_KEY not set]"

    import google.generativeai as genai
    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_VISION_MODEL)

    img = PIL.Image.open(image_path)
    
    prompt = (
        "This image was extracted from a business/financial document (chart, "
        "figure, logo, or photo). In 2-3 sentences, describe exactly what it "
        "shows. If it is a chart or graph, state the axis labels, the series "
        "names, and the key numeric values/trend you can read off it. Be "
        "precise with numbers - they may be used to answer financial questions."
    )
    
    try:
        resp = model.generate_content([prompt, img])
        return resp.text.strip()
    except Exception as e:
        return f"[Image - caption failed: {e}]"
