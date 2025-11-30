from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal

from .chatbot_logic import answer_with_rag

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "https://cs372-jc939.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
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
    # Convert Pydantic models to plain dicts
    history = [m.model_dump() for m in body.history]

    # 🔑 Multi-turn: pass history into RAG answerer
    reply = answer_with_rag(query=body.message, history=history, debug=True)

    return ChatResponse(reply=reply)
