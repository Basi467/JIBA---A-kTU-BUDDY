from __future__ import annotations

import logging
import os

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .limiter import limiter
from .routes import auth, chat, exam, meta, priority, progress, study_plan, subjects

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("jiba.api")

# No-ops when SENTRY_DSN is unset (the SDK's own documented behavior for a
# falsy dsn) — so this works identically in dev/CI without the user's own
# Sentry project, and goes live the moment the env var is set.
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.2,
    send_default_pii=False,
)

app = FastAPI(title="JIBA - A KTU Buddy API", version="1.0.0")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down and try again shortly."},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Preserve FastAPI's normal HTTPException behavior (401/404/409/etc. with
    # the detail message a route explicitly raised) — only unexpected errors
    # fall through to the catch-all handler below.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request data."})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    # FastAPI's own exception_handler intercepts before Sentry's ASGI
    # middleware would otherwise see it, so it's reported explicitly here
    # rather than relying on FastApiIntegration's automatic capture.
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


app.include_router(auth.router)
app.include_router(meta.router)
app.include_router(subjects.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(exam.router)
app.include_router(study_plan.router)
app.include_router(priority.router)


@app.get("/health")
def health():
    return {"status": "ok"}
