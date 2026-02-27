import logging
from chatbot.llm_engine import generate_llm_response
from models.price_model import predict_price
from models.yield_model import estimate_yield

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("ROLE ROUTER LOADED")


def process_chat(role, message, language="en"):

    logger.info(f"Processing role: {role}")

    # ================= PRICE DATA =================
    predicted_price, weekly_avg = predict_price()

    # ================= YIELD DATA =================
    land_size = 2
    soil_quality = 80
    rainfall = 8

    estimated_yield = estimate_yield(
        land_size,
        soil_quality,
        rainfall
    )

    price_delta = round(
        ((predicted_price - weekly_avg) / weekly_avg) * 100,
        2
    )

    final_decision = "ANALYZING"
    confidence = 50
    system_data = ""

    # ================= FARMER =================
    if role.lower() == "farmer":

        score = 0

        if price_delta > 5:
            score += 50
        elif price_delta > 0:
            score += 30
        else:
            score += 10

        if estimated_yield > 3000:
            score += 30
        elif estimated_yield > 2000:
            score += 20
        else:
            score += 10

        confidence = min(score, 100)

        if confidence > 70:
            final_decision = "SELL"
        elif confidence > 40:
            final_decision = "SELL WITH CAUTION"
        else:
            final_decision = "HOLD"

        system_data = f"""
Predicted Price: ₹{predicted_price}
Weekly Average: ₹{weekly_avg}
Price Change: {price_delta}%
Estimated Yield: {estimated_yield}
"""

    # ================= DISTRIBUTOR =================
    elif role.lower() == "distributor":

        transport_time = 5
        cold_chain_temp = 4
        warehouse_capacity = 80

        score = 0

        if transport_time < 6:
            score += 40
        if 2 <= cold_chain_temp <= 8:
            score += 40
        if warehouse_capacity < 90:
            score += 20

        confidence = min(score, 100)

        final_decision = (
            "LOW SPOILAGE RISK"
            if confidence > 70
            else "MONITOR COLD CHAIN"
        )

        system_data = f"""
Transport Time: {transport_time} days
Cold Chain Temperature: {cold_chain_temp}°C
Warehouse Usage: {warehouse_capacity}%
"""

    # ================= RETAILER =================
    elif role.lower() == "retailer":

        demand_index = 75

        score = 0

        if demand_index > 70:
            score += 50
        elif demand_index > 50:
            score += 30

        if predicted_price < weekly_avg:
            score += 30

        score += 20

        confidence = min(score, 100)

        if confidence > 70:
            final_decision = "REORDER NOW"
        elif confidence > 40:
            final_decision = "REORDER MODERATELY"
        else:
            final_decision = "WAIT"

        system_data = f"""
Demand Index: {demand_index}
Distributor Price: ₹{predicted_price}
Weekly Average: ₹{weekly_avg}
"""

    # ================= CONSUMER =================
    elif role.lower() == "consumer":

        traceability_score = 92
        freshness_score = 85
        allergy_risk = 10

        score = traceability_score * 0.4 + freshness_score * 0.4 - allergy_risk * 0.2
        confidence = int(min(max(score, 0), 100))

        if confidence > 75:
            final_decision = "SAFE TO BUY"
        elif confidence > 50:
            final_decision = "BUY WITH CAUTION"
        else:
            final_decision = "AVOID PURCHASE"

        system_data = f"""
Traceability Score: {traceability_score}/100
Freshness Score: {freshness_score}/100
Allergy Risk: {allergy_risk}/100
"""

    else:
        final_decision = "ROLE NOT SUPPORTED"
        confidence = 0
        system_data = "Invalid role."

    # ================= GENERATE RESPONSE =================
    response = generate_llm_response(
        role=role,
        message=message,
        system_data=system_data,
        final_decision=final_decision,
        confidence=confidence,
        language=language
    )

    return response