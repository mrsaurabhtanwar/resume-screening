import sys
import os
# from contextlib import asynccontextmanager
from fastapi import FastAPI

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers.jobdes import router as jobdes_router
from routers.upload import router as upload_router
# from routers.ranking import router as ranking_router, initialize_dataset
# from routers.candidates import router as candidate_router
# from routers.analytics import router as analytics_router
# from routers.qa import router as qa_router


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup: Pre-load dataset and FAISS vector index
#     print("[Startup] Initializing Candidate Intelligence Engine dataset & FAISS Index...")
#     # initialize_dataset()
#     print("[Startup] Initialization complete!")
#     yield
#     # Shutdown
#     print("[Shutdown] Cleaning up system resources.")

app = FastAPI(
    title="AI Resume Screening & Candidate Intelligence Engine API",
    description="Multi-signal candidate ranking, skill gap analysis, clustering, and recruiter Q&A API",
    version="1.1.0",
    # lifespan=lifespan
)

# Include Routers
app.include_router(jobdes_router)
app.include_router(upload_router)
# app.include_router(ranking_router)
# app.include_router(candidate_router)
# app.include_router(analytics_router)
# app.include_router(qa_router)


@app.get("/")
@app.get("/upload")
def simple_health_check():
    return {"message": "FastAPI backend is running", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
