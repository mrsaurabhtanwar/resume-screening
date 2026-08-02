import os
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routers.jobdes import router as jobdes_router
from routers.upload import router as upload_router
from routers.ranking import router as ranking_router
from routers.candidates import router as candidate_router
from services.embedding_service import get_embedding_model


def get_allowed_origins() -> list[str]:
    """Return explicit browser origins allowed to call the API cross-origin."""
    configured_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://127.0.0.1:8080,http://localhost:8080",
    )
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_embedding_model()
    yield

app = FastAPI(
    title="CVRanking API",
    description="PDF resume ingestion, candidate management, and job-description ranking API.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobdes_router)
app.include_router(upload_router)
app.include_router(ranking_router)
app.include_router(candidate_router)

# Serve the bundled dashboard when its assets are available. The environment
# override keeps the same application code usable from both the repository and
# the Docker image, where the frontend is copied to /app/frontend.
frontend_dir = Path(
    os.getenv("FRONTEND_DIR", str(Path(__file__).resolve().parent.parent / "frontend"))
)
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
