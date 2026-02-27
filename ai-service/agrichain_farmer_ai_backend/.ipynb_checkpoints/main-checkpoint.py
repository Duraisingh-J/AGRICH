from fastapi import FastAPI
from pydantic import BaseModel
from chatbot.role_router import process_chat

app = FastAPI()


class ChatRequest(BaseModel):
    role: str
    message: str
    session_id: str = "default"
    language: str = "en"   # NEW multilingual field


@app.post("/chat")
def chat(request: ChatRequest):

    response = process_chat(
        role=request.role,
        message=request.message,
        session_id=request.session_id,
        language=request.language
    )

    return {"response": response}