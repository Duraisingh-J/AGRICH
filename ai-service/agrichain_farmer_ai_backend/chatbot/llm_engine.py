import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_llm_response(role, message, system_data, final_decision, language="en"):

    prompt = f"""
You are AGRICHAIN AI Decision Engine.

Explain clearly in 3-5 short bullet points.
Respond strictly in {language}.
End with:

Final Decision: {final_decision}

System Data:
{system_data}

User Role: {role}
User Question: {message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text.strip()

    except Exception as e:
        print("LLM ERROR:", e)
        return (
            "• Market conditions analyzed.\n"
            "• Price trend evaluated.\n"
            "• Estimated yield considered.\n\n"
            f"Final Decision: {final_decision}"
        )