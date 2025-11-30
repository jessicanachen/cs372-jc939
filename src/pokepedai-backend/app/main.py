# backend/main.py

import logging
import time
from collections import defaultdict
from typing import Dict, List, Literal

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from .chatbot_logic import answer_with_rag

# ---------- Logging setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("pokepedia")

# ---------- Rate limiting (dependency-based) ----------

# In-memory storage for request counters:
# key = "<client_ip>:<route_path>" -> {"timestamp": int, "count": int}
request_counters: Dict[str, Dict[str, int]] = defaultdict(dict)


class RateLimiter:
    """
    Per-IP, per-route rate limiter.

    requests_limit: max number of requests allowed
    time_window:    window size in seconds
    """

    def __init__(self, requests_limit: int, time_window: int):
        self.requests_limit = requests_limit
        self.time_window = time_window

    async def __call__(self, request: Request):
        # Try to be robust if request.client is None
        client_ip = (
            request.client.host if request.client and request.client.host else "unknown"
        )
        route_path = request.url.path

        current_time = int(time.time())
        key = f"{client_ip}:{route_path}"

        # New client/route
        if key not in request_counters:
            request_counters[key] = {"timestamp": current_time, "count": 1}
        else:
            ts = request_counters[key]["timestamp"]
            count = request_counters[key]["count"]

            # If the time window has elapsed, reset the counter
            if current_time - ts > self.time_window:
                request_counters[key]["timestamp"] = current_time
                request_counters[key]["count"] = 1
            else:
                # Still in the same window
                if count >= self.requests_limit:
                    logger.warning(
                        "Rate limit exceeded for %s on %s (limit=%d in %ds)",
                        client_ip,
                        route_path,
                        self.requests_limit,
                        self.time_window,
                    )
                    # Raise HTTPException - FastAPI will handle this cleanly
                    raise HTTPException(
                        status_code=429,
                        detail="Too Many Requests",
                    )
                else:
                    request_counters[key]["count"] = count + 1

        # Optional: purge old entries
        for k in list(request_counters.keys()):
            if current_time - request_counters[k]["timestamp"] > self.time_window:
                request_counters.pop(k, None)

        return True


# ---------- App + CORS ----------

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


# ---------- Simple logging middleware ----------

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    start = time.time()
    logger.info(
        "Incoming request %s %s from %s",
        request.method,
        request.url.path,
        client_ip,
    )

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception while processing request")
        raise

    duration_ms = (time.time() - start) * 1000
    logger.info(
        "Completed %s %s with status=%s in %.1fms for %s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        client_ip,
    )
    return response


# ---------- Pydantic models ----------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    message: str


class ChatRequest(BaseModel):
    history: List[ChatMessage]
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------- Exception handlers ----------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # This will also catch 429 from RateLimiter
    logger.warning(
        "HTTPException %s on %s: %s",
        exc.status_code,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error."},
    )


# ---------- Routes ----------

@app.get("/")
def health_check():
    logger.debug("Health check called")
    return {"status": "ok"}


# Apply rate limiting to /chat via dependency:
# e.g. 10 requests per 60 seconds per IP for this route
@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(RateLimiter(requests_limit=10, time_window=60))],
)
def chat(body: ChatRequest):
    logger.info("Handling /chat request with %d history messages", len(body.history))

    try:
        history = [m.model_dump() for m in body.history]
        reply = answer_with_rag(query=body.message, history=history, debug=True)
        logger.info("Successfully generated reply for /chat")
        return ChatResponse(reply=reply)
    except HTTPException:
        # Re-raise HTTPExceptions (e.g. if answer_with_rag wants to)
        raise
    except Exception:
        logger.exception("Error while handling /chat")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate a reply.",
        )
