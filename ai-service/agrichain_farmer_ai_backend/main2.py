
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from models.disease_model import detect_disease
from models.price_model import predict_price
from models.yield_model import estimate_yield
from utils.recommendation import generate_recommendation

app = FastAPI(title="AGRICHAIN Farmer AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/farmer-analysis")
async def farmer_analysis(
    file: UploadFile = File(...),
    land_size: float = Form(...),
    rainfall: float = Form(...)
):
    try:
        image_bytes = await file.read()

        disease, confidence = detect_disease(image_bytes)
        disease_severity = confidence if confidence < 1 else 0.3

        estimated_yield = estimate_yield(
            land_size,
            rainfall,
            disease_severity
        )

        predicted_price = predict_price()
        estimated_revenue = round(estimated_yield * predicted_price, 2)

        recommendation = generate_recommendation(predicted_price)

        return {
            "disease": disease,
            "disease_confidence": confidence,
            "estimated_yield_kg": estimated_yield,
            "predicted_price_per_kg": predicted_price,
            "estimated_revenue": estimated_revenue,
            "recommendation": recommendation
        }

    except Exception as e:
        return {"error": str(e)}
