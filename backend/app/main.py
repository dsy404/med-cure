import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .api.routes import router, get_data_loader, get_search_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medledger")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MedLedger datasets, evidence store, and search engine...")
    loader = get_data_loader()
    engine = get_search_engine(loader)
    logger.info(f"Initialized search engine with {len(engine._generic_index)} generic and {len(engine._ceiling_index)} ceiling price records.")
    yield
    logger.info("MedLedger backend shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=f"{settings.TAGLINE} Evidence-first medicine savings intelligence platform.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the medicine record request.",
            "path": str(request.url.path)
        }
    )

@app.get("/")
def get_root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "api_health": "/api/health",
        "search_endpoint": "/api/medicines/search?q={query}"
    }

app.include_router(router, prefix=settings.API_V1_STR)
