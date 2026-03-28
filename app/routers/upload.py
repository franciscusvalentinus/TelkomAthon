import os
import shutil
import tempfile
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Document, DocumentChunk
from app.routers.auth import get_current_user
from app.services.parser import parse_document, chunk_text
from app.services.embedder import embed_chunks

router = APIRouter(tags=["documents"])

ALLOWED_TYPES = {"pdf", "pptx", "docx", "xlsx"}


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    results = []

    for file in files:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            raw_text = parse_document(tmp_path, ext)
        except Exception as e:
            os.unlink(tmp_path)
            raise HTTPException(status_code=422, detail=f"Failed to parse {file.filename}: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # Save document
        doc = Document(user_id=user_id, filename=file.filename, file_type=ext, content=raw_text)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Chunk + embed
        chunks = chunk_text(raw_text)
        vectors = embed_chunks(chunks)

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            db.add(DocumentChunk(
                document_id=doc.id,
                chunk_text=chunk,
                embedding=vector,
                chunk_index=idx,
            ))
        db.commit()

        results.append({"document_id": str(doc.id), "filename": file.filename, "chunks_created": len(chunks)})

    return {"uploaded": results}


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    docs = db.query(Document).filter(Document.user_id == user_id).order_by(Document.uploaded_at.desc()).all()
    return [
        {"document_id": str(d.id), "filename": d.filename, "file_type": d.file_type, "uploaded_at": d.uploaded_at}
        for d in docs
    ]
