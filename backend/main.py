import sys
import os
from fastapi import FastAPI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers.jobdes import router as jobdes_router
from routers.upload import router as upload_router
from routers.ranking import router as ranking_router
from routers.candidates import router as candidate_router


app = FastAPI(
    title="AI Resume Screening & Candidate Intelligence Engine API",
    description="Multi-signal candidate ranking, skill gap, clustering, and recruiter API",
    version="1.0.0",
)

# Include Routers
app.include_router(jobdes_router)
app.include_router(upload_router)
app.include_router(ranking_router)
app.include_router(candidate_router)


@app.get("/")
@app.get("/upload")
def simple_health_check():
    return {"message": "FastAPI backend is running", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
