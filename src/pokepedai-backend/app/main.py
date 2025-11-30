from fastapi import FastAPI
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
    allow_methods=["*"],   # or ["GET", "POST", "OPTIONS"]
    allow_headers=["*"],
)

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
