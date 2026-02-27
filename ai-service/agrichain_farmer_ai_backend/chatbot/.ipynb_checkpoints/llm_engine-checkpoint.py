import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-flash-latest")


def generate_llm_response(
    role,
    message,
    context,
    system_data="",
    history=None,
    final_decision=None,
    confidence=None,
    language="en"
):

    language_map = {
        "en": {
            "instruction": "Respond in English.",
            "decision_label": "FINAL DECISION",
            "confidence_label": "CONFIDENCE SCORE"
        },
        "ta": {
            "instruction": "Respond in Tamil.",
            "decision_label": "இறுதி தீர்மானம்",
            "confidence_label": "நம்பிக்கை மதிப்பீடு"
        },
        "hi": {
            "instruction": "Respond in Hindi.",
            "decision_label": "अंतिम निर्णय",
            "confidence_label": "विश्वास स्तर"
        },
        "te": {
            "instruction": "Respond in Telugu.",
            "decision_label": "చివరి నిర్ణయం",
            "confidence_label": "నమ్మక స్థాయి"
        },
        "ml": {
            "instruction": "Respond in Malayalam.",
            "decision_label": "അന്തിമ തീരുമാനം",
            "confidence_label": "വിശ്വാസ നില"
        },
        "kn": {
            "instruction": "Respond in Kannada.",
            "decision_label": "ಅಂತಿಮ ತೀರ್ಮಾನ",
            "confidence_label": "ನಂಬಿಕೆ ಮಟ್ಟ"
        }
    }

    lang_data = language_map.get(language, language_map["en"])

    prompt = f"""
You are AGRICHAIN AI Decision Engine for the {role} role.

{lang_data['instruction']}

Respond in:
• One-line summary
• 2–3 short bullet points (max 12 words each)
• Keep under 80 words

Use numeric values where possible.

System Data:
{system_data}

User Question:
{message}
"""

    response = model.generate_content(prompt)

    # Append translated decision block manually
    final_output = f"""{response.text.strip()}

{lang_data['decision_label']}: {final_decision}
{lang_data['confidence_label']}: {confidence}%"""

    return final_output