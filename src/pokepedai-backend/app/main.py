import logging
import time
from typing import List, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from .chatbot_logic import answer_with_rag
from .rate_limiter import RateLimiter

# logger setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("pokepedia.backend")

# pydandic models
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    message: str


class ChatRequest(BaseModel):
    history: List[ChatMessage]
    message: str


class ChatResponse(BaseModel):
    reply: str

def configure_cors(app):
    """
    Setup CORS
    """

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

def configure_exception_handlers(app):
    """
    Setup a generic exception handler and an http exception handler
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
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

def configure_middlewares(app):
    """
    Setup logging for requests (incoming requests, exceptions, completion status)
    """

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

def register_routes(app):
    """
    Setup chatbot route and health
    """

    @app.get("/")
    def health_check():
        logger.debug("Health check called")
        return {"status": "ok"}

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
            raise
        except Exception:
            logger.exception("Error while handling /chat")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate a reply.",
            )


def create_app():
    """
    Create FAST API app
    """

    app = FastAPI()
    configure_cors(app)
    configure_exception_handlers(app)
    configure_middlewares(app)
    register_routes(app)
    return app

app = create_app()
