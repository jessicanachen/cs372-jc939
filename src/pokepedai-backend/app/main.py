from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal

from .chatbot_logic import answer_with_rag

app = FastAPI()

class ChatMessage(BaseModel):
    role: Literal["user", "bot"]
    message: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    history = [m.model_dump() for m in body.history]
    reply = answer_with_rag(body.message, debug = True)
    return ChatResponse(reply=reply)
