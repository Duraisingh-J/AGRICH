from chatbot.rag_engine import retrieve_context
from chatbot.llm_engine import generate_llm_response
from models.price_model import predict_price, get_7day_average
from models.yield_model import estimate_yield

chat_sessions = {}


def process_chat(role, message, session_id="default", language="en"):

    context = retrieve_context(message, role)

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_sessions[session_id].append({"role": "user", "content": message})

    system_data = ""
    final_decision = "ANALYZING"
    confidence = 50

    # ================= FARMER =================
    if role == "farmer":

        predicted_price = predict_price()
        avg_price = get_7day_average()
        estimated_yield = estimate_yield(2, 80, 8, 120, 0.2)

        price_delta_percent = ((predicted_price - avg_price) / avg_price) * 100

        score = 0

        if price_delta_percent > 5:
            score += 50
        elif price_delta_percent > 0:
            score += 30
        else:
            score += 10

        if estimated_yield > 3000:
            score += 30
        elif estimated_yield > 2000:
            score += 20
        else:
            score += 10

        confidence = min(max(score, 0), 100)

        if confidence > 70:
            final_decision = "SELL"
        elif confidence > 40:
            final_decision = "SELL WITH CAUTION"
        else:
            final_decision = "HOLD"

        system_data = f"""
        Predicted price: {predicted_price}
        7-day average price: {avg_price}
        Price delta: {round(price_delta_percent,2)}%
        Estimated yield: {estimated_yield}
        Preliminary decision: {final_decision}
        Confidence score: {confidence}
        """

    # ================= DISTRIBUTOR =================
    elif role == "distributor":

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

        final_decision = "LOW SPOILAGE RISK" if confidence > 70 else "MONITOR COLD CHAIN"

        system_data = f"""
        Transport time: {transport_time}
        Cold chain temperature: {cold_chain_temp}
        Warehouse usage: {warehouse_capacity}%
        Preliminary decision: {final_decision}
        Confidence score: {confidence}
        """

    # ================= RETAILER =================
    elif role == "retailer":

        predicted_price = predict_price()
        avg_price = get_7day_average()
        demand_index = 75

        score = 0

        if demand_index > 70:
            score += 50
        elif demand_index > 50:
            score += 30

        if predicted_price < avg_price:
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
        Demand index: {demand_index}%
        Distributor price: {predicted_price}
        Weekly average: {avg_price}
        Preliminary decision: {final_decision}
        Confidence score: {confidence}
        """

    # ================= CONSUMER =================
    elif role == "consumer":

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
        Traceability score: {traceability_score}/100
        Freshness score: {freshness_score}/100
        Allergy risk: {allergy_risk}/100
        Preliminary decision: {final_decision}
        Confidence score: {confidence}
        """

    response = generate_llm_response(
        role=role,
        message=message,
        context=context,
        system_data=system_data,
        history=chat_sessions[session_id],
        final_decision=final_decision,
        confidence=confidence,
        language=language
    )

    chat_sessions[session_id].append({"role": "assistant", "content": response})

    return response