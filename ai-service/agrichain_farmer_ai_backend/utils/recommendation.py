
def generate_recommendation(predicted_price):
    if predicted_price > 25:
        return "High market demand. Sell within 3 days."
    elif predicted_price < 20:
        return "Prices low. Consider holding stock."
    else:
        return "Stable pricing. Monitor for 2-3 days."
