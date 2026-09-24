# app.py

import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import __version__, get_settings
from dependencies import require_auth
from routes.background import router as background_router
from routes.outreach import router as outreach_router
from routes.profile import router as profile_router
from routes.resume import router as resume_router
from routes.search import router as search_router

# Load .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
settings = get_settings()

# OpenAPI docs are public outside production only.
docs_enabled = not settings.is_production
app = FastAPI(
    title=settings.app_title,
    version=__version__,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

# ---- CORS (origins from CORS_ALLOW_ORIGINS) ----
allow_all = settings.cors_allow_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    # Browsers reject credentialed requests to a wildcard origin.
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Include Routers (all protected; /healthcheck stays public) ----
protected = [Depends(require_auth)]
for router in (resume_router, search_router, outreach_router, profile_router, background_router):
    app.include_router(router, dependencies=protected)


@app.get("/healthcheck", tags=["health"])
async def healthcheck():
    return {"status": "ok", "version": __version__}
