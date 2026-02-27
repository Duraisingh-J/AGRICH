import logging
from chatbot.llm_engine import generate_llm_response
from models.price_model import predict_price
from models.yield_model import estimate_yield

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logger.info("ROLE ROUTER FILE LOADED")


def process_chat(role, message, language="en"):

    logger.info("CHAT PROCESSING STARTED")

    # -----------------------------
    # 1️⃣ Price Prediction
    # -----------------------------
    predicted_price, weekly_avg = predict_price()

    # -----------------------------
    # 2️⃣ Yield Estimation
    # -----------------------------
    land_size = 2
    soil_quality = 80
    rainfall = 8

    estimated_yield = estimate_yield(
        land_size,
        soil_quality,
        rainfall
    )

    # -----------------------------
    # 3️⃣ Price Delta %
    # -----------------------------
    price_delta = round(
        ((predicted_price - weekly_avg) / weekly_avg) * 100,
        2
    )

    logger.info(f"Predicted Price: {predicted_price}")
    logger.info(f"Weekly Average: {weekly_avg}")
    logger.info(f"Price Delta: {price_delta}%")

    # -----------------------------
    # 4️⃣ Decision Logic (Farmer Focused)
    # -----------------------------
    if role.lower() == "farmer":
        if price_delta > 5:
            decision_key = "SELL"
        elif 2 < price_delta <= 5:
            decision_key = "SELL_CAUTION"
        else:
            decision_key = "HOLD"
    else:
        decision_key = "MAINTAIN"

    # -----------------------------
    # 5️⃣ Multilingual Decision Map
    # -----------------------------
    decision_map = {
        "SELL": {
            "en": "SELL",
            "ta": "விற்கவும்",
            "hi": "बेचें",
            "te": "అమ్మండి",
            "ml": "വിൽക്കുക",
            "kn": "ಮಾರಾಟ ಮಾಡಿ"
        },
        "SELL_CAUTION": {
            "en": "SELL WITH CAUTION",
            "ta": "எச்சரிக்கையுடன் விற்கவும்",
            "hi": "सावधानी से बेचें",
            "te": "జాగ్రత్తగా అమ్మండి",
            "ml": "ജാഗ്രതയോടെ വിൽക്കുക",
            "kn": "ಎಚ್ಚರಿಕೆಯಿಂದ ಮಾರಾಟ ಮಾಡಿ"
        },
        "HOLD": {
            "en": "HOLD",
            "ta": "காத்திருக்கவும்",
            "hi": "रोकें",
            "te": "వేచి ఉండండి",
            "ml": "കാത്തിരിക്കുക",
            "kn": "ನಿರೀಕ್ಷಿಸಿ"
        },
        "MAINTAIN": {
            "en": "MAINTAIN CURRENT LEVEL",
            "ta": "தற்போதைய நிலை தொடரவும்",
            "hi": "वर्तमान स्तर बनाए रखें",
            "te": "ప్రస్తుత స్థాయి కొనసాగించండి",
            "ml": "നിലവിലെ നില തുടരുക",
            "kn": "ಪ್ರಸ್ತುತ ಮಟ್ಟ ಮುಂದುವರಿಸಿ"
        }
    }

    final_decision = decision_map.get(decision_key, decision_map["HOLD"]).get(
        language,
        decision_map[decision_key]["en"]
    )

    # -----------------------------
    # 6️⃣ System Data Passed to LLM
    # -----------------------------
    system_data = f"""
Predicted Price: ₹{predicted_price}
Weekly Average: ₹{weekly_avg}
Estimated Yield: {estimated_yield}
Price Change Percentage: {price_delta}%
"""

    # -----------------------------
    # 7️⃣ Generate Final Explanation
    # -----------------------------
    response = generate_llm_response(
        role=role,
        message=message,
        system_data=system_data,
        final_decision=final_decision,
        language=language
    )

    logger.info("CHAT PROCESSING COMPLETED")

    return response