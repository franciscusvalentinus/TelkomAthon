from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.db.models import Syllabus, MicroModule, Recommendation
from app.routers.auth import get_current_user
from app.routers import auth, upload, syllabus, decompose, recommend

app = FastAPI(
    title="AI-Powered Curriculum Design & Micro-Learning Assistant",
    description="TelkomAthon 2025 — Tim LDD SoDSNP",
    version="1.0.0",
)

# CORS — allow Streamlit frontend (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(syllabus.router)
app.include_router(decompose.router)
app.include_router(recommend.router)


@app.get("/")
def root():
    return {"message": "LDD AI Assistant API is running"}


@app.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return all history (syllabi, micro modules, recommendations) for the current user."""
    user_id = current_user["user_id"]

    syllabi = db.query(Syllabus).filter(Syllabus.user_id == user_id).order_by(Syllabus.created_at.desc()).all()
    modules = db.query(MicroModule).filter(MicroModule.user_id == user_id).order_by(MicroModule.created_at.desc()).all()
    recs = db.query(Recommendation).filter(Recommendation.user_id == user_id).order_by(Recommendation.created_at.desc()).all()

    return {
        "syllabi": [
            {"id": str(s.id), "topic": s.topic, "level": s.level, "output_json": s.output_json, "created_at": s.created_at}
            for s in syllabi
        ],
        "micro_modules": [
            {
                "id": str(m.id), "title": m.title, "objective": m.objective,
                "summary": m.summary, "delivery_format": m.delivery_format,
                "duration_minutes": m.duration_minutes, "created_at": m.created_at,
            }
            for m in modules
        ],
        "recommendations": [
            {
                "id": str(r.id), "participant_name": r.participant_name,
                "gap_input": r.gap_input, "recommended_modules": r.recommended_modules,
                "created_at": r.created_at,
            }
            for r in recs
        ],
    }
