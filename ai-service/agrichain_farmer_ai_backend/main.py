from dotenv import load_dotenv
load_dotenv()   # 🔥 Load environment variables first

from fastapi import FastAPI
from pydantic import BaseModel
from chatbot.role_router import process_chat
import traceback

app = FastAPI()


class ChatRequest(BaseModel):
    role: str
    message: str
    language: str = "en"


@app.post("/chat")
def chat(request: ChatRequest):

    print("CHAT REQUEST RECEIVED")

    try:
        response = process_chat(
            role=request.role,
            message=request.message,
            language=request.language
        )

        return {"response": response}

    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()
        return {"response": "Internal server error."}