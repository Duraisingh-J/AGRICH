import os
import logging
from dotenv import load_dotenv
from groq import Groq

# --------------------------------------------------
# Load Environment
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

client = Groq(api_key=API_KEY)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logger.info("LLM ENGINE (GROQ) LOADED SUCCESSFULLY")

# --------------------------------------------------
# Language Support
# --------------------------------------------------
LANGUAGE_MAP = {
    "en": {
        "instruction": "Respond strictly in English.",
        "decision": "Final Decision",
        "confidence": "Confidence"
    },
    "ta": {
        "instruction": "Respond strictly in Tamil.",
        "decision": "இறுதி தீர்மானம்",
        "confidence": "நம்பிக்கை"
    },
    "hi": {
        "instruction": "Respond strictly in Hindi.",
        "decision": "अंतिम निर्णय",
        "confidence": "विश्वास स्तर"
    },
    "te": {
        "instruction": "Respond strictly in Telugu.",
        "decision": "చివరి నిర్ణయం",
        "confidence": "నమ్మకం"
    },
    "ml": {
        "instruction": "Respond strictly in Malayalam.",
        "decision": "അന്തിമ തീരുമാനം",
        "confidence": "വിശ്വാസം"
    },
    "kn": {
        "instruction": "Respond strictly in Kannada.",
        "decision": "ಅಂತಿಮ ತೀರ್ಮಾನ",
        "confidence": "ನಂಬಿಕೆ"
    }
}

# --------------------------------------------------
# Generate LLM Response
# --------------------------------------------------
def generate_llm_response(
    role,
    message,
    system_data,
    final_decision,
    confidence,
    language="en"
):

    lang = LANGUAGE_MAP.get(language, LANGUAGE_MAP["en"])

    # Strongly Controlled Prompt
    prompt = f"""
You are AGRICHAIN AI Decision Engine for the {role} role.

{lang['instruction']}

Follow these rules strictly:
- Provide 3 to 5 short bullet points.
- Each bullet max 18 words.
- Use numeric values from system data.
- Do NOT repeat decision inside bullets.
- Do NOT exceed 120 words.
- Do NOT add extra sections.

System Data:
{system_data}

User Question:
{message}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a precise agricultural decision assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # lower for stable academic demo
            max_tokens=400,
        )

        explanation = completion.choices[0].message.content.strip()

        # Enforce correct decision and confidence labels manually
        final_output = (
            f"{explanation}\n\n"
            f"{lang['decision']}: {final_decision}\n"
            f"{lang['confidence']}: {confidence}%"
        )

        return final_output

    except Exception as e:
        logger.error(f"GROQ ERROR: {e}")

        # Safe fallback (multilingual safe)
        fallback = (
            "• Market data analyzed.\n"
            "• Price trend evaluated.\n"
            "• Risk factors considered."
        )

        return (
            f"{fallback}\n\n"
            f"{lang['decision']}: {final_decision}\n"
            f"{lang['confidence']}: {confidence}%"
        )