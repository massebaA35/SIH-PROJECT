"""
Application entry point.

Wires together CORS, security headers, a lightweight in-memory rate
limiter, and every router. Run with:
    uvicorn app.main:app --reload --port 8010
"""
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    alerts, analyze, assistant, audit, auth, cases, dashboard,
    entities, graph, locations, reports, search, timeline,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Investigative decision-support prototype for the Ministry of Home Affairs, "
        "National Crime Records Bureau (Women Safety Division). All data is synthetic. "
        "AI-generated findings are presented only as potential connections, risk indicators, "
        "analytical leads, or items requiring investigator verification -- never as proof of guilt."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "0"  # modern browsers rely on CSP instead
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# Lightweight in-memory sliding-window rate limiter (per client IP). This is
# adequate for a single-process prototype; a production deployment behind
# multiple workers would move this to Redis or an API gateway.
_request_log: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _request_log[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please slow down."})
    window.append(now)
    return await call_next(request)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "notice": "Investigative decision-support prototype. Synthetic data only.",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": settings.environment}


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(cases.router)
app.include_router(entities.router)
app.include_router(graph.router)
app.include_router(alerts.router)
app.include_router(timeline.router)
app.include_router(locations.router)
app.include_router(analyze.router)
app.include_router(search.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(assistant.router)
