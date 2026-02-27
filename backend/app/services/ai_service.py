"""AI service stubs for AGRICHAIN intelligence features."""

import uuid


class AIService:
    """Stubbed AI service with async interfaces."""

    async def predict_price(self, crop_type: str, location: str) -> dict[str, str | float]:
        """Predict crop price for location (mock response)."""

        return {
            "crop_type": crop_type,
            "location": location,
            "predicted_price": 42.5,
            "currency": "INR/kg",
            "model_version": "mock-v1",
        }

    async def detect_disease(self, image_url: str) -> dict[str, str | float]:
        """Detect disease from image URL (mock response)."""

        return {
            "image_url": image_url,
            "disease": "leaf_blight",
            "confidence": 0.87,
            "model_version": "mock-v1",
        }

    async def spoilage_risk(self, batch_id: uuid.UUID) -> dict[str, str | float]:
        """Estimate spoilage risk for batch (mock response)."""

        return {
            "batch_id": str(batch_id),
            "risk": "medium",
            "score": 0.46,
            "model_version": "mock-v1",
        }

    async def fraud_score(self, user_id: uuid.UUID) -> dict[str, str | float]:
        """Calculate fraud score for user (mock response)."""

        return {
            "user_id": str(user_id),
            "fraud_score": 0.12,
            "risk_band": "low",
            "model_version": "mock-v1",
        }
